"""Prerequisite CPU implementations. No model loader, generator, or experiment launcher."""
from collections import defaultdict
import math
from .utils import ROOT,read,stable


def rectangle_cells(rect,source_pixels,processed_pixels):
    sx,sy=[p/s for p,s in zip(processed_pixels,source_pixels,strict=True)]
    width,height=processed_pixels
    if width%32 or height%32:raise ValueError('Non-merger-aligned processor geometry')
    x0=max(0,math.floor(rect['x']*sx/32));x1=min(width//32,math.ceil((rect['x']+rect['width'])*sx/32))
    y0=max(0,math.floor(rect['y']*sy/32));y1=min(height//32,math.ceil((rect['y']+rect['height'])*sy/32))
    return {y*(width//32)+x for y in range(y0,y1) for x in range(x0,x1)}


def source_closure(ledger,mapping,evidence,rectangles,processor):
    """Necessary selection-freedom test; does not certify full selector applicability.

    Protect global/unowned records and candidate x observed M/R/L. Resource-category
    protection can only remove further freedom, so this optimistic test may prove
    impossibility but cannot prove qualification. No selector features are fitted.
    """
    records=ledger['records'];by_source={r['source']:r for r in records}
    if len(by_source)!=len(records):raise ValueError('Duplicate source occurrence ID')
    cards={c['id']:c for c in evidence['cards']}
    if len(cards)!=len(evidence['cards']):raise ValueError('Duplicate card ID')
    rects={r['card']:r for r in rectangles}
    if set(rects)!=set(cards) or len(rects)!=len(rectangles):raise ValueError('Card/rectangle mismatch')
    parent={s:s for s in by_source}
    def find(s):
        while parent[s]!=s:parent[s]=parent[parent[s]];s=parent[s]
        return s
    def join(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    card_sources=defaultdict(set);source_cards=defaultdict(set)
    for item in mapping:
        if set(item)!={'source','path','binding','disposition','value_hash'}:raise ValueError('Unknown mapping structure')
        source=item['source']
        if source not in by_source:
            # The frozen compiler adds only these two graph-alias bindings.
            # They are not new source records; verify the actual drawn edge and
            # an original-record binding before excluding the duplicate alias.
            if source not in {'bound_relations','selected_calls'}:raise ValueError('Unknown source occurrence')
            binding=item['binding'];parts=binding.split('.') if binding else []
            if len(parts)!=3 or parts[1]!='edge' or parts[0] not in cards:raise ValueError('Unknown graph alias')
            edges=cards[parts[0]]['data']['edges'];edge=next((e for e in edges if e['id']==parts[2]),None)
            values=[] if edge is None else [edge['source'],edge['target'],edge['kind']]
            if not any(stable(v)==item['value_hash'] for v in values):raise ValueError('Graph alias value mismatch')
            if not any(m['source'] in by_source and m['binding']==binding for m in mapping):
                raise ValueError('Graph alias without original source')
            continue
        if item['binding'] is not None:
            card=item['binding'].split('.')[0]
            if card not in cards:raise ValueError('Unknown binding card')
            card_sources[card].add(source);source_cards[source].add(card)
    if set(card_sources)!=set(cards):raise ValueError('Unbound source card')
    for sources in card_sources.values():
        ordered=sorted(sources)
        for source in ordered[1:]:join(ordered[0],source)
    # Explicit original fact IDs connect windows to metric records, never entity equality.
    metrics=defaultdict(list)
    for r in records:
        if r['kind']=='assignment' and 'fact_id' in r['value']:
            metrics[r['value']['fact_id']].append(r['source'])
        elif r['kind']=='aux':metrics[r['value']['id']].append(r['source'])
    for r in records:
        if r['kind']=='window':
            matches=metrics.get(r['value']['id'],[])
            if len(matches)!=1:raise ValueError('Window lacks unique explicit metric source')
            join(r['source'],matches[0])
    pairs=defaultdict(list)
    for r in records:
        if r.get('pair_packet_id'):pairs[r['pair_packet_id']].append(r['source'])
    for members in pairs.values():
        for source in members[1:]:join(members[0],source)
    groups=defaultdict(list)
    for source in sorted(by_source):groups[find(source)].append(source)
    group_cards={g:set().union(*(source_cards[s] for s in sources)) for g,sources in groups.items()}
    cellsets={c:rectangle_cells(rects[c],processor['source_pixels'],processor['processed_pixels']) for c in cards}
    domains={g:set().union(*(cellsets[c] for c in cs)) for g,cs in group_cards.items()}
    mandatory=set();coverage=defaultdict(set)
    modality={'metric':'M','trace':'R','log':'L','trace_joint':'R'}
    for source,record in by_source.items():
        cs=source_cards[source];value=record['value']
        owners={cards[c].get('entity') for c in cs};owners.discard(None)
        for key in ('entity','service','entity_id'):
            if isinstance(value.get(key),str):owners.add(value[key])
        if isinstance(value.get('entities'),list):owners.update(value['entities'])
        owners.update(record.get('public_owners',[]))
        modes={modality[cards[c]['kind']] for c in cs if cards[c]['kind'] in modality}
        for key in ('region','evidence_source_display'):
            if value.get(key) in ('M','R','L'):modes.add(value[key])
        if record.get('pair_packet_id'):modes.add('R')
        if (len(owners)!=1 and not record.get('pair_packet_id')) or not cs or any(cards[c]['kind']=='graph' for c in cs):
            mandatory.add(find(source))
        if len(owners)==1 or record.get('pair_packet_id'):
          for owner in owners:
            if owner in ledger['candidates']:
                for mode in modes:coverage[(owner,mode)].add(source)
    for sources in coverage.values():mandatory.add(find(min(sources)))
    protected=set().union(*(domains[g] for g in mandatory))
    allcells=set().union(*domains.values())
    budget=math.floor(.60*(len(allcells)-len(protected)))
    optional=sorted(set(groups)-mandatory)
    feasible=[g for g in optional if len(domains[g]-protected)<=budget]
    # Adding one legal optional closure gives a genuinely different valid subset.
    choice=bool(feasible) and bool(allcells-protected)
    return {'schema':'SourceClosureNecessaryAuditV1','source_count':len(records),'source_ids_hash':stable(sorted(by_source)),
        'closure_count':len(groups),'protected_closures':len(mandatory),'optional_closures':len(optional),
        'total_geometry_cells':len(allcells),'protected_geometry_cells':len(protected),'optional_geometry_budget':budget,
        'feasible_single_optional_closures':len(feasible),'selection_freedom_upper_bound':choice,
        'status':'not_disproven' if choice else 'proven_no_optional_choice','qualification_pass':False,
        'coverage_cells':len(coverage),'closures':[{'id':g,'sources':groups[g],'cards':sorted(group_cards[g]),
            'protected':g in mandatory,'incremental_cells':len(domains[g]-protected)} for g in sorted(groups)],
        'pending':['resource_category_protection','typed_selector_descriptors','objectives_and_selection','cross_arm_and_historical_deduplication']}


def case_inputs(row):
    from RQs.RQ4_1.src.exps import ledger
    base=ROOT/row['base']
    public=read(ROOT/f"RQs/RQ3_21/preparation/compact_entity_v1/public/{row['id']}.json")
    packet=ledger(public)
    audit=read(base/'source_audit.json')
    if audit.get('status')!='passed' or audit['source_hash']!=packet['source_hash']:
        raise ValueError('Frozen source ledger integrity failed')
    proc=read(base/'processor_cpu.json');evidence=read(base/'evidence.json')
    selection=source_closure(packet,read(base/'mapping.json'),evidence,
                             read(base/'render/manifest.json')['rectangles'],proc)
    job={'id':row['id'],'html':str(base/'render/dashboard.html'),'source_pixels':proc['source_pixels'],
         'processed_pixels':proc['processed_pixels'],'min_font':18}
    return selection,job


def grouped_delta(query,key,value,g,beta,groups,bidirectional=True):
    """Vectorized source-local branch using installed native chunk recurrence.

    Inputs already contain original convolution/projection results. This helper
    alone is NOT the layer/cache integration and cannot qualify production P arms.
    """
    import torch
    from transformers.models.qwen3_5.modeling_qwen3_5 import torch_chunk_gated_delta_rule
    if query.shape[0]!=1:raise ValueError('Registered single-request branch')
    flat=[i for group in groups for i in group]
    if len(flat)!=len(set(flat)) or any(i<0 or i>=query.shape[1] for i in flat):raise ValueError('Overlapping/out-of-range groups')
    result=torch.zeros_like(value);buckets=defaultdict(list)
    for group in groups:
        if not group or group!=sorted(group):raise ValueError('Nonempty original-order group required')
        length=math.ceil(len(group)/64)*64
        buckets[length].append(group)
    for length,items in buckets.items():
        directions=[(group,False) for group in items]
        if bidirectional:directions += [(group,True) for group in items]
        packed=[]
        for tensor in (query,key,value,g,beta):
            batch=tensor.new_zeros((len(directions),length,*tensor.shape[2:]))
            for row,(group,reverse) in enumerate(directions):
                positions=list(reversed(group)) if reverse else group
                batch[row,:len(group)]=tensor[0,positions]
            packed.append(batch)
        output,_=torch_chunk_gated_delta_rule(*packed[:3],g=packed[3],beta=packed[4],
            chunk_size=64,initial_state=None,output_final_state=False,use_qk_l2norm_in_kernel=True)
        for row,(group,reverse) in enumerate(directions):
            positions=list(reversed(group)) if reverse else group
            result[0,positions]+=output[row,:len(group)]/(2 if bidirectional else 1)
    return result


def soft_image_reference(q,k,v,image_positions,prefix_stop,weight=.25):
    """Small CPU reference before original output gate/projection, never production."""
    import torch
    n=q.shape[-2]
    if not 0<=weight<=1:raise ValueError('Invalid mixture')
    if not image_positions or min(image_positions)<prefix_stop or max(image_positions)>=n:
        raise ValueError('Invalid image/prefix ranges')
    logits=(q@k.transpose(-1,-2))/math.sqrt(q.shape[-1])
    causal=torch.ones((n,n),dtype=torch.bool,device=q.device).tril()
    native=torch.softmax(logits.masked_fill(~causal,float('-inf')),dim=-1)@v
    if weight==0:return native
    allowed=torch.zeros(n,dtype=torch.bool,device=q.device);allowed[:prefix_stop]=True;allowed[image_positions]=True
    aux=torch.softmax(logits[...,image_positions,:].masked_fill(~allowed,float('-inf')),dim=-1)@v
    result=native.clone();result[...,image_positions,:]=(1-weight)*native[...,image_positions,:]+weight*aux
    return result


def source_units(packet,mapping,evidence):
    """P units join only explicit series/window IDs, NEVER an entire shared card."""
    records={r['source']:r for r in packet['records']};canonical={s:s for s in records}
    identities=defaultdict(list)
    for s,r in records.items():
        v=r['value'];fid=v.get('fact_id') if r['kind']=='assignment' else v.get('id') if r['kind']=='aux' else None
        if fid:identities[fid].append(s)
    for s,r in records.items():
        if r['kind']=='window':
            matches=identities[r['value']['id']]
            if len(matches)!=1:raise ValueError('Ambiguous explicit source/window match')
            canonical[s]=matches[0]
    card_units=defaultdict(set);excluded=set()
    for s,r in records.items():
        v=r['value']
        if r['kind'] in {'pair_binary','pair_continuous'}:
            for row in v['rows']:canonical[s+'/'+row[0]]='request_pair:'+row[0]
        if r['kind']=='identities' or (r['kind']=='assignment' and v['field'] in
                {'estimated_fault_window','observation_window','explicit_missingness','trace_summary_meta','denum_log_meta'}):
            excluded.add(canonical[s])
    for item in mapping:
        if item['source'] in records and item['binding']:
            s=item['source'];pair=item['path'].strip('/').split('/')[0]
            key=s+'/'+pair if records[s]['kind'] in {'pair_binary','pair_continuous'} else s
            if key not in canonical:raise ValueError('Unknown per-pair provenance path')
            card_units[item['binding'].split('.')[0]].add(canonical[key])
        elif item['source'] not in records and item['source'] not in {'bound_relations','selected_calls'}:
            raise ValueError('Unknown source alias')
    return canonical,card_units,excluded


def co_membership_change(groups,other):
    """Exact pair-set Jaccard distance without quadratic pair materialization."""
    from collections import Counter
    a={i:g for g,group in enumerate(groups) for i in group}
    b={i:g for g,group in enumerate(other) for i in group}
    if set(a)!=set(b):raise ValueError('SHAM changed eligible token set')
    choose=lambda n:n*(n-1)//2
    intersection=sum(choose(n) for n in Counter((a[i],b[i]) for i in a).values())
    na=sum(choose(len(g)) for g in groups);nb=sum(choose(len(g)) for g in other)
    union=na+nb-intersection
    return (na+nb-2*intersection)/union if union else 0.


def source_token_groups(row,packet,mapping,evidence,rectangles,processor,retained):
    import hashlib
    canonical,card_units,excluded=source_units(packet,mapping,evidence)
    support=read(ROOT/row['base']/'token_support.json')
    roles=read(ROOT/row['base']/'provenance.json')['roles']
    n=processor['image_tokens'];retained=list(retained)
    if retained!=sorted(set(retained)) or any(i<0 or i>=n for i in retained):raise ValueError('Invalid historical retained token sequence')
    cell_cards=defaultdict(set)
    for rect in rectangles:
        for token in rectangle_cells(rect,processor['source_pixels'],processor['processed_pixels']):
            cell_cards[token].add(rect['card'])
    owners=defaultdict(set);uncertain=set()
    # An actual anchor token is assigned only if ALL intersecting cards certify
    # one original source unit. Empty geometry alone never creates support.
    for token in support['anchors']:
        cards=cell_cards[token];units=set().union(*(card_units[c] for c in cards))
        if not cards or len(units)!=1 or units&excluded:uncertain.add(token)
        else:owners[token].update(units)
    for role in roles:
        source=role['source_occurrence'].split('/')[0]
        if source not in canonical:raise ValueError('Unknown numeric-role source')
        path=role['source_occurrence'].split('/')
        key='/'.join(path[:2]) if '/'.join(path[:2]) in canonical else source
        unit=canonical[key]
        tokens=support['roles'][role['id']]['foreground_possible_tokens']
        for token in tokens:
            if unit in excluded:uncertain.add(token)
            else:owners[token].add(unit)
    groups=defaultdict(list)
    for token in retained:
        if token not in uncertain and len(owners[token])==1:groups[next(iter(owners[token]))].append(token)
    groups={s:g for s,g in groups.items() if len(g)>=8}
    groups=dict(sorted(groups.items(),key=lambda item:(min(item[1]),item[0])))
    eligible=sorted(i for g in groups.values() for i in g)
    shuffled=sorted(eligible,key=lambda i:(hashlib.sha256(f'rq43-sham-v1|{row["id"]}|{i}'.encode()).digest(),i))
    sham={};offset=0
    for source,group in groups.items():sham[source]=sorted(shuffled[offset:offset+len(group)]);offset+=len(group)
    coverage=len(eligible)/len(retained) if retained else 0
    lengths=[len(g) for g in groups.values()]
    qualified=len(groups)>=2 and coverage>=.2
    # Sequence-slot permutation preserves each token's original MRoPE identity.
    ordered=list(groups.values());half=len(ordered)//2
    rotated=[i for g in ordered[half:]+ordered[:half] for i in g]
    permutation=dict(zip(eligible,rotated,strict=True))
    return {'schema':'SourceLocalTokenGroupsV1','id':row['id'],'dataset':row['dataset'],
        'retained':retained,'groups':groups,'sham_groups':sham,'eligible_tokens':len(eligible),
        'retained_tokens':len(retained),'coverage':coverage,'qualified':qualified,
        'shared_or_global_retained':sum(i in uncertain or len(owners[i])!=1 for i in retained),
        'padded_tokens_one_direction':sum(math.ceil(n/64)*64 for n in lengths),
        'sham_change':co_membership_change(list(groups.values()),list(sham.values())),
        'order_token_source_by_slot':[[i,permutation[i]] for i in eligible],
        'qualification_scope':'geometry_and_source_support_not_feature_isolation'}


class VisualPrefillAdapter:
    """Instance-local hooks: preserve native projections, norm, state and decode.

    Activated explicitly around one complete image prefill; no weights, loader,
    generation, or externally visible diagnostic text is created by this class.
    """
    def __init__(self,model,groups,image_positions,mode='P_LOCAL_BI',weight=.25,reference_kernel=None):
        import copy
        from transformers.models.qwen3_5 import modeling_qwen3_5 as native
        allowed={'P_LOCAL_BI','P_SOFT_IMAGE','P_DUAL','C_LOCAL_FORWARD','C_SHAM_BI','C_GLOBAL_BI'}
        if mode not in allowed or not 0<=weight<=1:raise ValueError('Unregistered prefill operation')
        self.mode=mode;self.weight=weight
        self.groups=[sorted(i for g in groups for i in g)] if mode=='C_GLOBAL_BI' and groups else groups
        self.image_positions=list(image_positions)
        if self.image_positions!=list(range(min(image_positions),max(image_positions)+1)):
            raise ValueError('Exactly one contiguous image patch sequence required')
        if any(i not in self.image_positions for g in groups for i in g):raise ValueError('Nonimage token in local group')
        self.active=False;self.restore=[];self.branch_calls=0;self.reference_kernel=reference_kernel
        layers=model.layers if hasattr(model,'layers') else model.model.language_model.layers
        if mode!='P_SOFT_IMAGE':
            for layer in layers[:3]:
                module=layer.linear_attn;original=module.chunk_gated_delta_rule
                def mixed(q,k,v,*args,_original=original,**kwargs):
                    out,state=_original(q,k,v,*args,**kwargs)
                    if not self.active or self.weight==0 or kwargs.get('initial_state') is not None or not self.groups:
                        return out,state
                    if q.shape[1]<=max(self.image_positions):raise ValueError('Image prefill was split or truncated')
                    g=kwargs['g'];beta=kwargs['beta'];bidirectional=self.mode!='C_LOCAL_FORWARD'
                    if self.reference_kernel is None:
                        aux=grouped_delta(q,k,v,g,beta,self.groups,bidirectional)
                    else:
                        import torch
                        aux=torch.zeros_like(v)
                        for group in self.groups:
                            directions=[group,list(reversed(group))] if bidirectional else [group]
                            for positions in directions:
                                aux[:,positions]+=self.reference_kernel(q[:,positions],k[:,positions],v[:,positions],g[:,positions],beta[:,positions])/len(directions)
                    indexes=sorted(i for group in self.groups for i in group)
                    out=out.clone();out[:,indexes]=(1-self.weight)*out[:,indexes]+self.weight*aux[:,indexes]
                    self.branch_calls+=1
                    return out,state
                module.chunk_gated_delta_rule=mixed
                self.restore.append(lambda module=module,original=original:setattr(module,'chunk_gated_delta_rule',original))
        if mode in {'P_SOFT_IMAGE','P_DUAL'}:
            module=layers[3].self_attn;original_config=module.config
            original=native.ALL_ATTENTION_FUNCTIONS.get_interface(original_config._attn_implementation,native.eager_attention_forward)
            module.config=copy.copy(original_config);module.config._attn_implementation='rq43_soft_image_v1'
            # The registry dispatches per-instance; other layers keep their original config.
            def dispatch(layer,q,k,v,mask,**kwargs):
                owner=layer._rq43_adapter
                output,weights=layer._rq43_native_attention(layer,q,k,v,mask,**kwargs)
                if not owner.active or owner.weight==0 or q.shape[-2]<=1:return output,weights
                if q.shape[-2]!=k.shape[-2] or q.shape[-2]<=max(owner.image_positions):
                    raise ValueError('SOFT_IMAGE requires complete uncached prompt prefill')
                import torch
                import torch.nn.functional as F
                keys=list(range(min(owner.image_positions)))+owner.image_positions
                kk=native.repeat_kv(k,layer.num_key_value_groups);vv=native.repeat_kv(v,layer.num_key_value_groups)
                valid=None
                if mask is not None:
                    if mask.ndim!=4:raise ValueError('Unknown native attention mask layout')
                    # Last image query already sees all valid prefix/image keys
                    # under the native causal mask; preserve any padding exclusions.
                    last=mask[:,:,max(owner.image_positions),keys]
                    valid=(last if last.dtype==torch.bool else last>=0)[:,:,None,:]
                aux=F.scaled_dot_product_attention(q[:,:,owner.image_positions],kk[:,:,keys],vv[:,:,keys],
                    attn_mask=valid,dropout_p=0.,is_causal=False,scale=layer.scaling).transpose(1,2)
                output=output.clone()
                output[:,owner.image_positions]=(1-owner.weight)*output[:,owner.image_positions]+owner.weight*aux
                owner.branch_calls+=1
                return output,weights
            native.ALL_ATTENTION_FUNCTIONS.register('rq43_soft_image_v1',dispatch)
            module._rq43_adapter=self;module._rq43_native_attention=original
            def restore_attention():
                module.config=original_config
                del module._rq43_adapter;del module._rq43_native_attention
            self.restore.append(restore_attention)

    def prefill(self):
        from contextlib import contextmanager
        @contextmanager
        def active():
            if self.active:raise RuntimeError('Nested image prefill')
            self.active=True
            try:yield self
            finally:self.active=False
        return active()

    def close(self):
        for undo in reversed(self.restore):undo()
        self.restore.clear();self.active=False


def language_groups(packet,image_start,sham=False):
    positions={original:image_start+i for i,original in enumerate(packet['retained'])}
    return [[positions[i] for i in group] for group in packet['sham_groups' if sham else 'groups'].values()]


def reorder_visual_prefix(embeddings,position_ids,packet,image_start,rope_delta):
    """Move original spatial coordinates WITH tokens, leave text/causal slots fixed."""
    import torch
    if embeddings.shape[0]!=1 or position_ids.shape[0] not in (3,4):raise ValueError('Unknown MRoPE layout')
    positions={original:image_start+i for i,original in enumerate(packet['retained'])}
    pairs=packet['order_token_source_by_slot']
    slots=torch.tensor([positions[a] for a,b in pairs],device=embeddings.device)
    sources=torch.tensor([positions[b] for a,b in pairs],device=embeddings.device)
    out=embeddings.clone();coords=position_ids.clone()
    out[:,slots]=embeddings[:,sources];coords[-3:,:,slots]=position_ids[-3:,:,sources]
    return out,coords,rope_delta


def type7(values,p):
    values=sorted(v for v in values if v is not None)
    if not values:return None
    if not 0<=p<=1 or any(isinstance(v,bool) or not math.isfinite(v) for v in values):raise ValueError('Invalid quantile inputs')
    h=(len(values)-1)*p;i=math.floor(h);j=math.ceil(h)
    return values[i]*(j-h)+values[j]*(h-i) if i!=j else values[i]


def midranks(values):
    indexed=sorted(enumerate(values),key=lambda item:item[1]);result=[0.]*len(values);start=0
    while start<len(values):
        stop=start+1
        while stop<len(values) and indexed[stop][1]==indexed[start][1]:stop+=1
        rank=(start+stop-1)/2
        for i,_ in indexed[start:stop]:result[i]=rank/(len(values)-1) if len(values)>1 else .5
        start=stop
    return result


def selection_descriptors(packet,public,provenance,closure):
    """Typed public features; excluded anomaly fields can never be read as scores."""
    from RQs.RQ4_1.src.exps import numeric
    from RQs.RQ4_1.src.utils import decode_sequence
    owner_type=lambda owner:{3:'service',4:'node',5:'pod'}.get(len(owner),'external')
    group_of={s:c['id'] for c in closure['closures'] for s in c['sources']}
    result=[];seen_windows=set();phase_indexes=defaultdict(lambda:defaultdict(set))
    for role in provenance['roles']:
        source=role['source_occurrence'].split('/')[0]
        if role['phase'] in ('reference','current'):
            for target in role['targets']:
                if '.sample.' in target['binding']:
                    phase_indexes[source][role['phase']].add(int(target['binding'].rsplit('.',1)[1]))
    def add(s,owners,mode,key,values,changes,paths,identifier=None):
        if not owners or mode not in ('M','R','L'):return
        if any(isinstance(v,bool) or not math.isfinite(v) for v in values+changes):raise ValueError('Invalid feature value')
        result.append({'id':identifier or s,'source':s,'closure':group_of[s],'owners':owners,'entity_key':tuple(owners),
            'modality':mode,'key':tuple(key),'values':values,'changes':changes,'source_paths':paths})
    for record in packet['records']:
        s=record['source'];v=record['value'];kind=record['kind'];field=v.get('field')
        owner=v.get('entity',v.get('service',v.get('entity_id')))
        if kind=='window':continue  # Same explicit packet as the original sequence/operation.
        if kind=='assignment' and field=='metric_series_64' or kind=='aux':
            seq=[numeric(x) if x is not None else None for x in decode_sequence(v['values_codec'])]
            phases=phase_indexes[s];groups={}
            for phase in ('reference','current'):
                indexes=sorted(phases.get(phase,set()))
                if any(i>=len(seq) for i in indexes):raise ValueError('Phase/source index mismatch')
                vals=[seq[i] for i in indexes if seq[i] is not None]
                if vals:groups[phase]=[type7(vals,p) for p in (.1,.5,.9)]
            values=[type7(seq,p) for p in (.1,.5,.9)] if not groups and any(x is not None for x in seq) else [x for phase in sorted(groups) for x in groups[phase]]
            changes=[b-a for a,b in zip(groups['reference'],groups['current'],strict=True)] if set(groups)=={'reference','current'} else []
            # source_unit is an honest unknown unit, not evidence of cross-entity comparability.
            unit=v['unit'];verified=bool(unit) and unit not in {'source_unit','unknown','?'}
            key=('metric',owner_type(owner),v['metric'],unit,tuple(sorted(groups)) or ('window',))
            if not verified:key=('unknown_unit_singleton',s)
            if values:add(s,[owner],'M',key,values,changes if verified else [],['/values_codec','/unit'])
        elif kind=='assignment' and field=='trace_summary_entry':
            values=[];changes=[];paths=[]
            for name,unit in (('exl_p95','µs'),('count','count')):
                a=v.get(name+'_base_us' if name=='exl_p95' else name+'_base')
                b=v.get(name+'_fault_us' if name=='exl_p95' else name+'_fault')
                if a is None or b is None:continue
                a,b=numeric(a),numeric(b)
                add(s,[owner],'R',('trace',owner_type(owner),v['operation'],name,unit),[a,b],[b-a],
                    ['/exl_p95_base_us','/exl_p95_fault_us'] if name=='exl_p95' else ['/count_base','/count_fault'],s+':'+name)
        elif kind=='assignment' and field=='denum_log_template':
            add(s,[owner],'L',('log',owner_type(owner),v['template'],v['level'],'count','relative_bin',str(v['relative_bin'])),
                [numeric(v['count'])],[],['/count','/relative_bin','/template','/level'])
        elif kind=='pair_continuous':
            for relation in public['payload']['relations']:
                if record.get('pair_packet_id') and relation['id']!=record['pair_packet_id']:continue
                phases=relation['phases'];values=[];stats={}
                for phase in ('reference','current'):
                    points=phases[phase]['points'];stats[phase]=[]
                    for endpoint in (0,1):stats[phase]+=[type7([numeric(p[endpoint]) for p in points],q) for q in (.1,.5,.9)]
                    stats[phase].append(numeric(phases[phase]['n']));values+=stats[phase]
                key=('pair',owner_type(relation['parent']),owner_type(relation['child']),relation['parent_operation'],relation['child_operation'],'ms_and_count')
                add(s,[relation['parent'],relation['child']],'R',key,values,[b-a for a,b in zip(stats['reference'],stats['current'],strict=True)],
                    [f"/{relation['id']}/reference/points",f"/{relation['id']}/current/points"],s+':'+relation['id'])
        else:
            mode=v.get('region',v.get('evidence_source_display'))
            if owner and mode in ('M','R','L'):
                add(s,[owner],mode,('uncomparable_singleton',s),[],[],[])
    represented={d['source'] for d in result}
    for r in packet['records']:
        if r['source'] in represented or r['kind'] in {'window','pair_binary','pair_continuous'}:continue
        v=r['value'];owner=v.get('entity',v.get('service',v.get('entity_id')))
        mode={'metric_series_64':'M','trace_summary_entry':'R','denum_log_template':'L'}.get(v.get('field'))
        if r['kind']=='aux':mode='M'
        if owner and mode:add(r['source'],[owner],mode,('uncomparable_singleton',r['source']),[],[],[])
    # Normalize multiple feature families of ONE source packet before objectives.
    return result


def selection_objectives(descriptors):
    """Dense small CPU matrices; no model features or historical outcomes."""
    import numpy as np
    n=len(descriptors);sim=np.eye(n);distance=np.zeros((n,n));groups=defaultdict(list)
    for i,d in enumerate(descriptors):groups[(d['key'],len(d['values']),len(d['changes']))].append(i)
    edge_groups=[]
    for indexes in groups.values():
        if not indexes:continue
        if descriptors[indexes[0]]['values']:
            ranks=np.asarray([midranks([descriptors[i]['values'][j] for i in indexes]) for j in range(len(descriptors[indexes[0]]['values']))]).T
            for a,i in enumerate(indexes):
                for b,j in enumerate(indexes):sim[i,j]=1-float(abs(ranks[a]-ranks[b]).mean())
        if descriptors[indexes[0]]['changes']:
            ranks=np.asarray([midranks([descriptors[i]['changes'][j] for i in indexes]) for j in range(len(descriptors[indexes[0]]['changes']))]).T
            pairs=defaultdict(list)
            for a,i in enumerate(indexes):
                for b,j in enumerate(indexes[a+1:],a+1):
                    if descriptors[i]['entity_key']==descriptors[j]['entity_key']:continue
                    entities=tuple(sorted((descriptors[i]['entity_key'],descriptors[j]['entity_key'])))
                    pairs[entities].append((i,j,float(abs(ranks[a]-ranks[b]).mean())))
            if pairs:edge_groups.append(pairs)
    for pairs in edge_groups:
        for members in pairs.values():
            for i,j,d in members:distance[i,j]=d/(len(edge_groups)*len(pairs)*len(members))
    weights=np.zeros(n);modalities=sorted({d['modality'] for d in descriptors})
    for mode in modalities:
        owners=sorted({o for d in descriptors if d['modality']==mode for o in d['owners']})
        for owner in owners:
            indexes=[i for i,d in enumerate(descriptors) if d['modality']==mode and owner in d['owners']]
            sources=sorted({descriptors[i]['source'] for i in indexes})
            for source in sources:
                members=[i for i in indexes if descriptors[i]['source']==source]
                for i in members:weights[i]+=1/(len(modalities)*len(owners)*len(sources)*len(members))
    return sim,distance,weights


def greedy_source_selection(closure,descriptors,domains,oid,method):
    import hashlib
    import numpy as np
    sim,dist,weights=selection_objectives(descriptors)
    selected={c['id'] for c in closure['closures'] if c['protected']}
    protected=set().union(*(domains[g] for g in selected));allcells=set().union(*domains.values())
    budget=math.floor(.60*(len(allcells)-len(protected)));full_dist=float(dist.sum());full_rep=float(weights.sum())
    group_ids=[d['closure'] for d in descriptors]
    def objectives(chosen):
        indexes=[i for i,g in enumerate(group_ids) if g in chosen]
        d=float(dist[np.ix_(indexes,indexes)].sum()) if indexes else 0.
        r=float((weights*sim[:,indexes].max(axis=1)).sum()) if indexes else 0.
        return d,r
    def value(chosen):
        d,r=objectives(chosen)
        return d if method=='S_DISTINGUISH' else r if method=='S_REPRESENT' else .5*(d/full_dist if full_dist else 0)+.5*(r/full_rep if full_rep else 0)
    used=set(protected);accepted=[]
    pairs={tuple(sorted((group_ids[i],group_ids[j]))) for i,j in zip(*np.nonzero(dist)) if group_ids[i]!=group_ids[j]}
    if method!='C_SOURCE_HASH':
        for _ in range(len(domains)):
            remaining=set(domains)-selected;proposals={(g,) for g in remaining}
            if method!='S_REPRESENT':proposals|={tuple(g for g in pair if g in remaining) for pair in pairs if set(pair)&remaining}
            candidates=[];current=value(selected)
            for proposal in proposals:
                cells=set().union(*(domains[g] for g in proposal));increment=len(cells-used)
                if len((used|cells)-protected)>budget:continue
                gain=value(selected|set(proposal))-current
                if gain<=1e-14:continue
                candidates.append((-(gain/increment) if increment else float('-inf'),-gain,increment,proposal,cells))
            if not candidates:break
            best=min(candidates,key=lambda x:x[:4]);selected.update(best[3]);used|=best[4]
            accepted.append({'closures':list(best[3]),'gain':-best[1],'new_cells':best[2]})
    filled=[]
    for group in sorted(set(domains)-selected,key=lambda g:(hashlib.sha256(f'rq43-fill-v1|{oid}|{g}'.encode()).digest(),g)):
        cells=domains[group]
        if len((used|cells)-protected)<=budget:selected.add(group);used|=cells;filled.append(group)
    d,r=objectives(selected)
    return {'selected':sorted(selected),'optional_budget':budget,'used_optional_cells':len(used-protected),
        'distinguish_objective':d,'represent_objective':r,'full_distinguish':full_dist,'full_represent':full_rep,
        'greedy_steps':accepted,'hash_filled':filled,'changed_from_full':selected!=set(domains)}


def sp_case(row):
    from .utils import HISTORY
    from RQs.RQ4_1.src.exps import ledger
    base=ROOT/row['base'];public=read(ROOT/f"RQs/RQ3_21/preparation/compact_entity_v1/public/{row['id']}.json")
    packet=ledger(public);mapping=read(base/'mapping.json');evidence=read(base/'evidence.json')
    if read(base/'source_audit.json')['source_hash']!=packet['source_hash']:raise ValueError('Frozen ledger hash mismatch')
    proc=read(base/'processor_cpu.json');rectangles=read(base/'render/manifest.json')['rectangles']
    selection_packet,selection_mapping=selection_packet_projection(packet,mapping,public)
    closure=source_closure(selection_packet,selection_mapping,evidence,rectangles,proc)
    source_group={s:c['id'] for c in closure['closures'] for s in c['sources']}
    resources=defaultdict(list)
    # Preserve each publicly named resource metric category, without guessing
    # CPU/memory/disk classes from anomaly names or private fault annotations.
    for r in selection_packet['records']:
        v=r['value'];owner=v.get('entity',v.get('service'))
        if (r['kind']=='aux' or v.get('field')=='metric_series_64') and isinstance(owner,str) and len(owner) in (4,5):
            resources[(owner,v['metric'])].append(r['source'])
    protected_resources={source_group[min(ss)] for ss in resources.values()}
    for c in closure['closures']:c['protected']=c['protected'] or c['id'] in protected_resources
    rects={r['card']:r for r in rectangles}
    domains={c['id']:set().union(*(rectangle_cells(rects[cid],proc['source_pixels'],proc['processed_pixels']) for cid in c['cards'])) for c in closure['closures']}
    descriptors=selection_descriptors(selection_packet,public,read(base/'provenance.json'),closure)
    selections={method:greedy_source_selection(closure,descriptors,domains,row['id'],method) for method in
        ['S_DISTINGUISH','S_REPRESENT','S_JOINT','C_SOURCE_HASH']}
    for selection in selections.values():
        chosen=set(selection['selected'])
        if not {c['id'] for c in closure['closures'] if c['protected']}<=chosen:raise ValueError('Mandatory packet lost')
        if selection['used_optional_cells']>selection['optional_budget']:raise ValueError('Source budget exceeded')
        selection['sources']=sorted(s for c in closure['closures'] if c['id'] in chosen for s in c['sources'])
        selection['cards']=sorted({cid for c in closure['closures'] if c['id'] in chosen for cid in c['cards']})
        selection['original_occurrence_records_hash']=stable([r for r in selection_packet['records'] if r['source'] in selection['sources']])
    historical_key=f"{row['id']}__development__A_UNIFORM_E50__BASE"
    # Only execution metadata is projected. Historical responses/scores are never features.
    old=read(HISTORY/f'formal_v28/completed/{historical_key}.json')
    retained=old['actual_retention']['indices']
    if old['image_tokens_original']!=proc['image_tokens'] or old['gather_plan']['selected_visual_indices']!=retained:
        raise ValueError('Historical gather/processor identity mismatch')
    groups=source_token_groups(row,packet,mapping,evidence,rectangles,proc,retained)
    return {'id':row['id'],'dataset':row['dataset'],'status':'completed','selection':selections,
        'resource_categories_protected':len(resources),'descriptors':descriptors,'groups':groups,
        'source_hash':packet['source_hash'],'historical_request_key':historical_key,
        'historical_metadata_only':True,'original_png_reused':True,'new_model_calls':0,
        'pending':['actual_S_renders_and_processor_masks','QA_compilation','historical_compatibility_certificate','deployment_runner']}


def selection_packet_projection(packet,mapping,public):
    """Expand explicit request-table ROW occurrences, preserving every original row.

    Numeric equality never merges observations. Binary/continuous rows with the
    same public PAIR ID are the two halves of that registered request packet.
    """
    import copy
    result=copy.deepcopy(packet);result['records']=[];by_source={r['source']:r for r in packet['records']}
    relations={r['id']:r for r in public['payload']['relations']}
    for record in packet['records']:
        if record['kind'] not in {'pair_binary','pair_continuous'}:result['records'].append(record);continue
        restored=[]
        for i,row in enumerate(record['value']['rows']):
            pair=row[0]
            if pair not in relations:raise ValueError('Unknown request pair')
            relation=relations[pair];expanded=copy.deepcopy(record)
            expanded.update(source=record['source']+'/'+pair,pair_packet_id=pair,
                public_owners=[relation['parent'],relation['child']],original_source=record['source'],original_row=i)
            expanded['value']['rows']=[row];result['records'].append(expanded);restored+=expanded['value']['rows']
        if restored!=record['value']['rows']:raise ValueError('Source row occurrence loss')
    projected=[]
    for item in mapping:
        entry=dict(item);record=by_source.get(entry['source'])
        if record and record['kind'] in {'pair_binary','pair_continuous'}:
            pair=entry['path'].strip('/').split('/')[0]
            if pair not in relations:raise ValueError('Pair binding lacks explicit pair ID')
            entry['source']+='/'+pair
        projected.append(entry)
    return result,projected


def reflow_job(row,folder,profile='source_reflow_v3'):
    """Existing registered components; measure complete unchanged field strings."""
    from renderer.utils import node_link_layout,source_graph_layout
    base=ROOT/row['base'];evidence=read(base/'evidence.json');design=read(base/'design.json')
    rects=read(base/'render/geometry.json')['rectangles']
    components={r['card']:r['component'] for r in rects}
    graphs=[c for c in evidence['cards'] if c['kind']=='graph']
    return {'evidence':str(base/'evidence.json'),'output':str(folder/'dom.json'),
        'profile':profile,'font_size':18,'region_widths':[512,768,1024],
        'components':components,'full_width_cards':[c['id'] for c in evidence['cards']],
        'indexing':design['indexing'],
        'node_layouts':{str(w):{c['id']:(source_graph_layout(c,w,18) if components[c['id']]=='graph.source_compact' else node_link_layout(c,w,18,tight=True)) for c in graphs} for w in (512,768,1024)}}


def reflow_layouts(row,measurement,profile='source_reflow_v3'):
    """Bounded v6 reflow. No diagnostic feedback, text compression or resizing."""
    from copy import deepcopy
    base=ROOT/row['base'];original=read(base/'design.json');evidence=read(base/'evidence.json')
    rects=read(base/'render/geometry.json')['rectangles'];nodes={}
    def visit(n):
        if n['type']=='panel':nodes[n['card']]=deepcopy(n)
        for child in n.get('children',[]):visit(child)
    visit(original['tree'])
    # Preserve the frozen evidence-card sequence; shortest-column assignment is
    # a declared layout algorithm, not anomaly- or outcome-based prioritization.
    order=[c['id'] for c in evidence['cards']]
    maximum=read(base/'processor_cpu.json')['image_tokens'];options=[]
    for m in measurement['measurements']:
        w=m['region_width'];sizes={r['card']:r for r in m['cards']}
        if set(sizes)!=set(order):raise ValueError('Reflow measurement lost a card')
        issues=[r['card'] for r in m['cards'] if r['overflow'] or r['min_font']<17.999]
        for count in range(2,8192//w+1):
            heights=[0]*count;cols=[[] for _ in heights]
            for cid in sorted(order,key=lambda cid:(-sizes[cid]['height'],order.index(cid))):
                k=min(range(count),key=lambda j:(heights[j],j));h=sizes[cid]['height']
                cols[k].append((cid,h));heights[k]+=h
            height=math.ceil((max(heights)+86)/32)*32;width=count*w
            viable=height<=8192 and width*height//1024<=maximum and not issues
            design=deepcopy(original);design.pop('provenance',None)
            design.update(viewport={'width':width,'height':height},gap=0,padding=0,
                font_size=18,readable_cards=profile,tree={'id':'reflow','type':'row','weights':[1]*count,'children':[]})
            for k,col in enumerate(cols):
                children=[nodes[cid] for cid,h in col];weights=[h for cid,h in col]
                spare=height-86-sum(weights)
                if spare:children.append({'id':f'blank{k}','type':'spacer'});weights.append(spare)
                design['tree']['children'].append({'id':f'column{k}','type':'column','children':children,'weights':weights})
            options.append({'width':width,'height':height,'card_width':w,'area':width*height,
                'estimated_image_tokens':width*height//1024,'original_image_token_cap':maximum,
                'dom_problem_cards':issues,'candidate_pass':viable,'design':design})
    # Reuse the existing four-region placement operation for mixed widths.
    # Whole cards choose their smallest measured non-overflow area, then stable
    # shortest-column placement; no source or field is removed or factored.
    from renderer.operations.evidence_regions import apply
    measures={m['region_width']:{r['card']:r for r in m['cards']} for m in measurement['measurements']}
    heights=[32]*8;panels=[];boxes=[];issues=[]
    mixed_order=sorted(order,key=lambda cid:(-min(measures[w][cid]['height'] for w in (512,1024)),order.index(cid)))
    for cid in mixed_order:
        choices=[measures[w][cid] for w in (512,1024) if not measures[w][cid]['overflow'] and measures[w][cid]['min_font']>=17.999]
        if not choices:issues.append(cid);choices=[measures[512][cid]]
        selected=min(choices,key=lambda r:(r['width']*r['height'],r['height'],r['width']))
        w,h=int(selected['width']),selected['height']
        if w==1024:
            region=min(range(4),key=lambda j:(max(heights[2*j:2*j+2]),j));k=2*region;y=max(heights[k:k+2]);heights[k:k+2]=[y+h]*2
        else:k=min(range(8),key=lambda j:(heights[j],j));y=heights[k];heights[k]+=h
        panels.append(nodes[cid]);boxes.append({'x':k*512,'y':y,'width':w,'height':h})
    height=max(heights);design=deepcopy(original);design.pop('provenance',None)
    design.update(viewport={'width':4096,'height':height},gap=0,padding=0,font_size=18,readable_cards=profile)
    apply(design,panels,boxes)
    options.append({'width':4096,'height':height,'card_width':'mixed_512_1024','area':4096*height,
        'estimated_image_tokens':4*height,'original_image_token_cap':maximum,'dom_problem_cards':issues,
        'candidate_pass':height<=8192 and 4*height<=maximum and not issues,'design':design})
    if any(n.get('component','').endswith('.source_compact') for n in nodes.values()):
        from renderer.utils import compile_design
        for option in options:
            if option['card_width']=='mixed_512_1024':continue
            if option['width']%128 or (option['width']//option['card_width'])%4:option['candidate_pass']=False;continue
            if option['height']>8192:option['candidate_pass']=False;continue
            scene=compile_design(evidence,option['design'])
            boxes=[dict(x=r['x'],y=r['y']+10,width=r['width'],height=r['height']) for r in scene['rectangles']]
            height=math.ceil(max(b['y']+b['height'] for b in boxes)/32)*32
            option['design']['viewport']['height']=height
            apply(option['design'],[nodes[r['card']] for r in scene['rectangles']],boxes)
            option.update(height=height,area=height*option['width'],estimated_image_tokens=height*option['width']//1024)
            option['candidate_pass']=height<=8192 and option['estimated_image_tokens']<=maximum and not option['dom_problem_cards']
    return sorted(options,key=lambda x:(x['area'],x['height'],x['width']))


def reflow_probe(rows,folder,profile='source_reflow_v3'):
    from renderer.measure import measure_jobs
    from renderer.main import render
    from .utils import save,HISTORY,digest
    folder.mkdir(parents=True,exist_ok=True);jobs=[]
    for row in rows:
        d=folder/row['id'];d.mkdir(exist_ok=True);jobs.append(reflow_job(row,d,profile))
    save(folder/'jobs.json',jobs);measure_jobs(folder/'jobs.json',folder/'measure.log');out=[]
    for row in rows:
        d=folder/row['id'];measurement=read(d/'dom.json')
        if profile=='source_scopes_v2':
            # The old generic meter reports DOM height; graph compile also
            # enforces its registered node layout's explicit minimum height.
            job=next(j for j in jobs if j['output']==str(d/'dom.json'))
            for m in measurement['measurements']:
                for card in m['cards']:
                    graph=job['node_layouts'][str(m['region_width'])].get(card['card'])
                    if graph:card['height']=max(card['height'],math.ceil(graph['min_height']/32)*32)
        options=reflow_layouts(row,measurement,profile)
        save(d/'layouts.json',options);good=[x for x in options if x['candidate_pass']]
        result={'id':row['id'],'dataset':row['dataset'],'layout_count':len(options),'capacity_candidates':len(good),
            'best_area_tokens':options[0]['estimated_image_tokens'],'original_N':options[0]['original_image_token_cap'],
            'qualified':False,'new_model_calls':0}
        if good:
            selected=good[0];base=ROOT/row['base'];design=selected['design']
            # Foreground instrumentation is the renderer's registered audit
            # operation; it does not change model-visible data or pixels.
            if (base/'provenance.json').exists():
                design['provenance']={'schema':('CanonicalForegroundV3' if profile in {'source_scopes_v2','source_scopes_pack_v4'} else 'CanonicalForegroundV2'),'roles':[
                    {k:r[k] for k in ('id','targets')} for r in read(base/'provenance.json')['roles']]}
            save(d/'design.json',design)
            try:
                manifest=render(base/'evidence.json',d/'design.json',d/'render')
                result.update(render_status=manifest['status'],png_sha256=digest(d/'render/dashboard.png'))
            except Exception as exc:
                result.update(render_status='failed',error=str(exc))
        else:result['status']='no_capacity_layout_in_registered_finite_set'
        save(d/'result.json',result);out.append(result)
    save(folder/'report.json',out);return out


def selected_dashboard(base,cards):
    """Real registered panels or unlabelled spacers; retain exact kept geometry."""
    from copy import deepcopy
    from renderer.utils import compile_design
    evidence=read(base/'evidence.json');design=read(base/'design.json');keep=set(cards)
    original=compile_design(evidence,design)
    if not keep or not keep<={c['id'] for c in evidence['cards']}:raise ValueError('Selection references unknown/empty cards')
    def visit(node):
        if node['type']=='panel' and node['card'] not in keep:
            return {'id':node['id'],'type':'spacer'}
        result=deepcopy(node)
        if 'children' in node:result['children']=[visit(n) for n in node['children']]
        return result
    design['tree']=visit(design['tree']);evidence['cards']=[c for c in evidence['cards'] if c['id'] in keep]
    if 'indices' in design['indexing']:design['indexing']['indices']={k:v for k,v in design['indexing']['indices'].items() if k in keep}
    for key in ('presentation',):
        if key in design:design[key]={k:v for k,v in design[key].items() if k in keep}
    for key in ('bindings','relation_bindings'):
        if key in design:design[key]=[x for x in design[key] if x['card'] in keep and x['graph'] in keep]
    prov=read(base/'provenance.json');roles=[]
    for role in prov['roles']:
        present=[t['binding'].split('.')[0] in keep for t in role['targets']]
        if any(present) and not all(present):raise ValueError('Selection split an indivisible foreground role')
        if all(present):roles.append(role)
    prov['roles']=roles;role_ids={r['id'] for r in roles}
    prov['edges']=[e for e in prov['edges'] if set(e['roles'])<=role_ids]
    design['provenance']={'schema':'CanonicalForegroundV2','roles':[{k:r[k] for k in ('id','targets')} for r in roles]}
    scene=compile_design(evidence,design)
    if scene['rectangles']!=[r for r in original['rectangles'] if r['card'] in keep]:raise ValueError('Selection changed retained panel geometry')
    return evidence,design,prov


def uniform_support_indices(support,limit=None):
    """Same spatial FPS as historical UNIFORM, without unused feature tensors."""
    import numpy as np
    from scipy.ndimage import distance_transform_edt
    h,w=support['grid'];n=w*h
    if n!=support['image_tokens']:raise ValueError('Support grid mismatch')
    anchor=set(support['anchors']);eligible=sorted({t for r in support['roles'].values() for t in r['tokens']})
    if anchor&set(eligible):raise ValueError('Optional support contains mandatory anchors')
    target=len(anchor)+math.ceil(.5*len(eligible)) if limit is None else min(limit,len(anchor)+len(eligible))
    if target<len(anchor):raise ValueError('Mandatory anchors exceed retained-token ceiling')
    xy=np.asarray([[i%w,i//w] for i in range(n)],np.float32);taken=np.zeros(n,bool);taken[list(anchor)]=True
    # Integer grid distances are exactly representable here. EDT is an exact
    # nearest-anchor initializer, independently compared with the old loop.
    nearest=np.rint(distance_transform_edt(~taken.reshape(h,w))**2).reshape(-1) if anchor else np.full(n,np.inf)
    order=[];domain=np.zeros(n,bool);domain[eligible]=True
    while len(anchor)+len(order)<target:
        remaining=np.flatnonzero(domain&~taken)
        if not len(remaining):raise ValueError('Uniform budget exceeds available real evidence')
        t=int(remaining[np.argmax(nearest[remaining])]) if anchor or order else int(remaining[np.argmin(((xy[remaining]-xy.mean(0))**2).sum(1))])
        taken[t]=True;order.append(t);nearest=np.minimum(nearest,((xy-xy[t])**2).sum(1))
    return {'indices':np.flatnonzero(taken).tolist(),'optional_order':order,'anchor_count':len(anchor),'image_tokens':n}


def exact_panel_pixels(original,new,rectangles):
    import numpy as np
    from PIL import Image
    with Image.open(original) as a,Image.open(new) as b:
        if a.size!=b.size:raise ValueError('Selected dashboard changed canvas')
        for r in rectangles:
            box=(r['x'],r['y'],r['x']+r['width'],r['y']+r['height'])
            if not np.array_equal(np.asarray(a.crop(box)),np.asarray(b.crop(box))):
                raise ValueError('Retained panel pixels changed: '+r['card'])
    return True


def processor_audit(processor,png,prompt,maximum,retained=None):
    import torch
    from PIL import Image
    with Image.open(png) as image:
        size=image.size;batch=processor(text=[prompt],images=[image.convert('RGB')],return_tensors='pt')
    grid=batch['image_grid_thw'][0].tolist();n=math.prod(grid)//4
    if grid[0]!=1 or n>maximum:raise ValueError('Image token budget exceeded')
    if batch['pixel_values'].shape[0]!=math.prod(grid) or not torch.isfinite(batch['pixel_values']).all():raise ValueError('Processor corrupted patch tensor')
    input_tokens=int(batch['input_ids'].shape[-1]);text_tokens=input_tokens-n
    if input_tokens+8192>40960:raise ValueError('Full image context ceiling exceeded')
    if retained is not None and (retained!=sorted(set(retained)) or any(t<0 or t>=n for t in retained)):
        raise ValueError('Invalid retained sequence')
    result={'grid_thw':grid,'source_pixels':list(size),'processed_pixels':[grid[2]*16,grid[1]*16],
        'image_tokens':n,'full_input_tokens':input_tokens,'text_tokens':text_tokens,
        'retained_input_tokens':text_tokens+len(retained) if retained is not None else None,
        'prompt_sha256':stable(prompt),'pixel_tensor_shape':list(batch['pixel_values'].shape)}
    del batch;return result


def selected_prompt(prompt):
    """Neutral scope correction; no incident facts or new diagnostic strategy."""
    old='the complete telemetry dashboard. All incident observations and the exhaustive candidate IDs are in the image.'
    new='the available telemetry dashboard. The displayed observations and the exhaustive candidate IDs are in the image.'
    if prompt.count(old)!=1:raise ValueError('Unknown historical task interface')
    return prompt.replace(old,new)


QA_INSTRUCTION = '''Answer six factual reading questions using only the dashboard, not a root-cause ranking.
Q1: transcribe the scalar marked Q1. Q2: give that scalar's entity ID and unit.
Q3: compare the original values at the two metric samples Q3a and Q3b (a_greater, b_greater or equal). Compare data values, not positions on the page. These are two recorded samples; their markers imply no causal order.
Q4: transcribe the Trace/log scalar marked Q4. Q5: give its entity ID, unit and reference/current phase as displayed.
Q6: identify the source ID, relationship type and target ID of the directed edge marked Q6. That edge is thicker but retains its original type color and arrow direction.
Question labels and pointers identify existing evidence and add no answers. Use unavailable when the target or required fact is absent or unreadable. Copy IDs from the target entity, without a service/node/pod prefix. Keep original units; do not infer causality or convert units.
Return only JSON with keys q1,q2,q3,q4,q5,q6. q1/q4 are numeric strings or unavailable; q2 is {"entity_id":"...","unit":"..."} or unavailable; q3 is a_greater/b_greater/equal/unavailable; q5 is {"entity_id":"...","unit":"...","phase":"..."} or unavailable; q6 is {"source":"...","type":"...","target":"..."} or unavailable.'''


def mechanism_rows():
    from .utils import roster
    output=[]
    for dataset in ('aiops2022','aiops2025','aegislab'):
        pool=sorted((r for r in roster() if r['dataset']==dataset),key=lambda r:__import__('hashlib').sha256(('rq43-mechanism-v1|'+r['id']).encode()).hexdigest())
        chosen=[];seen=set()
        for row in pool:
            if row['event_group'] not in seen:chosen.append(row);seen.add(row['event_group'])
            if len(chosen)==20:break
        if len(chosen)<20:chosen.extend(r for r in pool if r not in chosen)
        output.extend(chosen[:20])
    return output


def factual_questions(row):
    """Fixed pool and private-to-QA answers, never labels or historical RCA."""
    from decimal import Decimal
    from RQs.RQ4_1.src.exps import scalar_target
    base=ROOT/row['base'];evidence=read(base/'evidence.json');mapping=read(base/'mapping.json');prov=read(base/'provenance.json')
    cards={c['id']:c for c in evidence['cards']};compiled={'evidence':evidence,'mapping':mapping};scalars=[]
    for role in prov['roles']:
        target=scalar_target(compiled,role)
        if target is None:continue
        card=cards[target['target']['binding'].split('.')[0]]
        # Binding QA needs an actual visible unit and reference/current label.
        text=' '.join([card['unit'],card['title']]+[d['name'] for d in card['data'].get('details',[])])
        unit=target['binding_answer']['unit']
        if unit.replace('_',' ') not in text.replace('_',' '):continue
        target['kind']=card['kind'];target['card']=card['id'];scalars.append(target)
    def choose(kind):
        eligible=[x for x in scalars if x['kind'] in kind and (x['kind']=='metric' or x['binding_answer']['phase'] in {'reference','current'})]
        return min(eligible,key=lambda x:stable(['rq43-qa-scalar-v1',row['id'],sorted(kind),x['source'],x['path']])) if eligible else None
    metric=choose({'metric'});other=choose({'trace','log'});questions={};targets=[]
    for name,value,bindq,tag in [('q1',metric,'q2','Q1'),('q4',other,'q5','Q4')]:
        if value is None:
            questions[name]={'applicable':False};questions[bindq]={'applicable':False};continue
        target=dict(tag=tag,**value['target']);targets.append(target)
        questions[name]={'applicable':True,'answer':value['display'],'kind':'numeric','target_tags':[tag],
            'source':value['source'],'path':value['path'],'card':value['card'],'unit':value['binding_answer']['unit'],
            'integer_count':value['binding_answer']['unit'] in {'count','events','requests','samples'}}
        fields=('entity_id','unit') if bindq=='q2' else ('entity_id','unit','phase')
        questions[bindq]={'applicable':True,'answer':{k:value['binding_answer'][k] for k in fields},
            'kind':'binding','target_tags':[tag],'card':value['card']}
    questions['q3']={'applicable':False}
    if metric:
        card=cards[metric['card']];values=card['data']['values'];finite=[i for i,v in enumerate(values) if v is not None and math.isfinite(v)]
        phases={t['binding']:r['phase'] for r in prov['roles'] for t in r['targets']}
        span=max((Decimal(str(values[i])) for i in finite),default=Decimal(0))-min((Decimal(str(values[i])) for i in finite),default=Decimal(0))
        pairs=[(a,b) for a in finite for b in finite if a<b and span>0 and abs(Decimal(str(values[a]))-Decimal(str(values[b])))>=span/10]
        cross=[(a,b) for a,b in pairs if {phases.get(f"{card['id']}.sample.{a}"),phases.get(f"{card['id']}.sample.{b}")}=={'reference','current'}]
        if pairs:
            a,b=min(cross or pairs,key=lambda pair:stable(['rq43-qa-point-v1',row['id'],card['id'],pair]))
            targets.extend({'tag':tag,'binding':f"{card['id']}.sample.{i}",'part':'all'} for tag,i in [('Q3a',a),('Q3b',b)])
            questions['q3']={'applicable':True,'kind':'comparison','answer':'a_greater' if values[a]>values[b] else 'b_greater',
                'target_tags':['Q3a','Q3b'],'card':card['id'],'sample_indices':[a,b],'original_values':[values[a],values[b]],
                'comparison_scope':'reference_current' if cross else 'within_window'}
    edges=[(c,e) for c in cards.values() if c['kind']=='graph' for e in c['data']['edges']]
    questions['q6']={'applicable':False}
    if edges:
        card,edge=min(edges,key=lambda ce:stable(['rq43-qa-edge-v1',row['id'],ce[0]['id'],ce[1]['id']]))
        targets.append({'tag':'Q6','binding':f"{card['id']}.edge.{edge['id']}",'part':'all'})
        questions['q6']={'applicable':True,'kind':'relation','answer':{'source':edge['source'],'type':edge['kind'],'target':edge['target']},
            'target_tags':['Q6'],'card':card['id'],'edge_id':edge['id']}
    return {'schema':'RQ43FactualQAV1','id':row['id'],'questions':questions,'targets':targets,
        'instruction':QA_INSTRUCTION,'answers_audit_only':True}


def qa_case(row,dest,processor):
    from renderer.main import render
    from RQs.RQ4_1.src.utils import foreground_support
    from .utils import save,HISTORY,digest
    packet=factual_questions(row);base=ROOT/row['base'];design=read(base/'design.json');design['factual_qa']=packet['targets']
    # All surviving QA methods share the same full U image and question targets.
    original=read(base/'processor_cpu.json');design['provenance']=read(base/'design.json')['provenance']
    save(dest/'packet_audit.json',packet);save(dest/'design.json',design)
    manifest=render(base/'evidence.json',dest/'design.json',dest/'render')
    if manifest['status']!='passed':raise ValueError('QA renderer audit failed')
    prompt=processor.apply_chat_template([{'role':'system','content':'Read the marked public telemetry facts accurately.'},
        {'role':'user','content':[{'type':'image'},{'type':'text','text':QA_INSTRUCTION}]}],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    support=foreground_support(dest/'render',original['processed_pixels'],policy='shared_v2')
    if support['definite_empty_unanchored_roles'] or support['uncertain_empty_unanchored_roles']:raise ValueError('QA source support unresolved')
    k=len(read(HISTORY/f"formal_v28/completed/{row['id']}__development__A_UNIFORM_E50__BASE.json")['actual_retention']['indices'])
    selected=uniform_support_indices(support,k);actual=processor_audit(processor,dest/'render/dashboard.png',prompt,original['image_tokens'],selected['indices'])
    save(dest/'token_support.json',support);save(dest/'retention.json',selected);save(dest/'processor.json',actual)
    save(dest/'prompt.json',{'prompt':prompt})
    # Required scalar labels, entity/units and edge are mandatory anchors;
    # sample endpoints also receive visible marker anchors. Audit exact support.
    from RQs.RQ4_1.src.exps import ledger
    public=read(ROOT/f"RQs/RQ3_21/preparation/compact_entity_v1/public/{row['id']}.json");prov=read(base/'provenance.json')
    save(dest/'provenance.json',prov)
    groups=source_token_groups(dict(row,base=str(dest.relative_to(ROOT))),ledger(public),read(base/'mapping.json'),
        read(base/'evidence.json'),manifest['rectangles'],actual,selected['indices']);save(dest/'groups.json',groups)
    targets={m['tag']:m for m in manifest['factual_qa']};kept=set(selected['indices']);anchors=set(support['anchors'])
    if not anchors<=kept:raise ValueError('QA mandatory glyph support lost')
    target_support={}
    for tag,target in targets.items():
        roles=[r for r in prov['roles'] if any(t['binding']==target['binding'] for t in r['targets'])]
        required=set().union(*(set(support['roles'][r['id']]['foreground_possible_tokens']) for r in roles))
        box=target['target_box']
        region=dict(x=box['x']-1,y=box['y']-1,width=box['width']+2,height=box['height']+2)
        required&=set(rectangle_cells(region,actual['source_pixels'],actual['processed_pixels']))
        if not required and tag!='Q6':raise ValueError('QA target lacks independently measured source ink: '+tag)
        target_support[tag]={'source_roles':[r['id'] for r in roles],'required_tokens':sorted(required),
            'retained_tokens':sorted(required&kept),'complete_ink_support':required<=kept,
            'relation_is_mandatory_anchor':tag=='Q6'}
    visibility={q:bool(v['applicable'] and all(target_support[t]['complete_ink_support'] for t in v['target_tags']))
        for q,v in packet['questions'].items()}
    # This is conservative geometric availability, not proof of correct reading.
    # Binding/phase strings and graph directions are mandatory anchor glyphs.
    for q in ('q1','q4'):
        question=packet['questions'][q]
        if question['applicable'] and targets[question['target_tags'][0]]['display']!=question['answer']:
            raise ValueError('Displayed QA scalar differs from source-derived answer')
    save(dest/'target_support.json',target_support)
    save(dest/'visibility.json',visibility)
    return {'id':row['id'],'dataset':row['dataset'],'status':'completed','applicable_questions':sum(v['applicable'] for v in packet['questions'].values()),
        'png_sha256':digest(dest/'render/dashboard.png'),'processor':actual,'P_source_qualified':groups['qualified'],
        'full_cpu_qualified':False,'new_model_calls':0}


def selected_followup():
    """Affected prompt accounting and source geometry on committed S images.

    Does not redraw, load weights, generate answers or certify full CPU scope.
    """
    import statistics
    from transformers import AutoProcessor
    from RQs.RQ4_1.src.exps import ledger
    from .utils import RQ,HISTORY,save,roster,code_identity,digest,checkpoint_sources
    root=RQ/'results/cpu_render_v6';population=root/'population01';dest=root/'followup01'
    if (dest/'phase_complete.json').exists():raise RuntimeError('Preserve completed followup; no overwrite')
    if read(population/'report.json')['errors']:raise ValueError('Population errors remain')
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    prompts={k:v['prompt'] for k,v in read(HISTORY/'deployment_v26/request_index.json')['requests'].items() if k.endswith('__VISUAL__BASE')}
    identity=code_identity();before=checkpoint_sources();rows=roster();spot={}
    for dataset in ('aiops2022','aiops2025','aegislab'):
        spot[dataset]=min((r['id'] for r in rows if r['dataset']==dataset),key=lambda s:stable(['rq43-prompt-spot-v6',s]))
    results=[];prompt_cache={}
    for row in rows:
        original=ROOT/row['base'];prompt=prompts[row['id']+'__VISUAL__BASE'];revised=selected_prompt(prompt)
        if prompt not in prompt_cache:
            oldids=processor.tokenizer(prompt,add_special_tokens=False)['input_ids']
            newids=processor.tokenizer(revised,add_special_tokens=False)['input_ids']
            imageid=processor.tokenizer.convert_tokens_to_ids('<|image_pad|>')
            if oldids.count(imageid)!=1 or newids.count(imageid)!=1:raise ValueError('Unexpected image placeholder')
            prompt_cache[prompt]=(len(oldids)-1,len(newids)-1)
        oldtext,newtext=prompt_cache[prompt];completed=read(population/f"completed/{row['id']}.json")
        record={'id':row['id'],'dataset':row['dataset'],'prompt_sha256':stable(revised),'S':{}}
        for arm in ('S_JOINT','C_SOURCE_HASH'):
            imagebase=population/f"inputs/{row['id']}/{arm}";previous=read(imagebase/'processor.json')
            if previous['text_tokens']!=oldtext or previous['prompt_sha256']!=stable(prompt):raise ValueError('Prompt accounting drift')
            kept=read(imagebase/'retention.json')['indices'];updated=dict(previous,text_tokens=newtext,
                full_input_tokens=previous['image_tokens']+newtext,retained_input_tokens=len(kept)+newtext,prompt_sha256=stable(revised))
            if updated['full_input_tokens']+8192>40960:raise ValueError('Revised context exceeds capacity')
            if row['id']==spot[row['dataset']]:
                actual=processor_audit(processor,imagebase/'render/dashboard.png',revised,previous['image_tokens'],kept)
                if actual!=updated:raise ValueError('Tokenizer update disagrees with actual multimodal processor')
            support=read(imagebase/'token_support.json')
            if support['definite_empty_unanchored_roles'] or support['uncertain_empty_unanchored_roles']:
                raise ValueError('Historical empty-support resolution needs individual requalification')
            save(dest/f"inputs/{row['id']}/{arm}/processor.json",updated)
            record['S'][arm]={'processor':updated,'image_reused_without_redraw':True,'kept_pixels_equal':True}
        # Only the public ledger is used. Historical responses are never input.
        public=read(ROOT/f"RQs/RQ3_21/preparation/compact_entity_v1/public/{row['id']}.json");packet=ledger(public)
        if read(original/'source_audit.json')['source_hash']!=packet['source_hash']:raise ValueError('Frozen public ledger mismatch')
        imagebase=population/f"inputs/{row['id']}/S_JOINT"
        evidence=read(imagebase/'evidence.json');ids={c['id'] for c in evidence['cards']}
        mapping=[m for m in read(original/'mapping.json') if m.get('binding') and m['binding'].split('.')[0] in ids]
        group_row=dict(row,base=str(imagebase.relative_to(ROOT)))
        groups=source_token_groups(group_row,packet,mapping,evidence,read(imagebase/'render/manifest.json')['rectangles'],
            read(imagebase/'processor.json'),read(imagebase/'retention.json')['indices'])
        record['X_SP_geometry']={k:groups[k] for k in ('coverage','qualified','sham_change','retained_tokens','eligible_tokens')}
        save(dest/f"inputs/{row['id']}/X_SP/groups.json",groups);save(dest/f"completed/{row['id']}.json",record);results.append(record)
    summary={}
    for dataset in spot:
        subset=[r for r in results if r['dataset']==dataset];summary[dataset]={
            'cases':len(subset),'X_SP_geometry_qualified':sum(r['X_SP_geometry']['qualified'] for r in subset),
            'X_SP_coverage_min_median_max':[fn(r['X_SP_geometry']['coverage'] for r in subset) for fn in (min,statistics.median,max)],
            'mean_retained_input':{arm:statistics.mean(r['S'][arm]['processor']['retained_input_tokens'] for r in subset) for arm in ('S_JOINT','C_SOURCE_HASH')}}
    protected=before==checkpoint_sources()
    if not protected:raise ValueError('Protected dependencies changed during followup')
    report={'schema':'RQ43AffectedFollowupV6','status':'passed','code_identity':identity,'completed':len(results),
        'by_dataset':summary,'actual_multimodal_processor_spot_ids':spot,'actual_processor_spots':6,
        'recomputed_prompt_token_counts_all_cases':True,'redrawn_images':0,'historical_sources_unchanged':protected,
        'scope':'S_scope_prompt_and_X_SP_geometry_only','full_cpu_qualified':False,'new_model_calls':0,
        'gpu_smoke_run':False,'formal_started':False}
    save(dest/'prompts.json',{stable(selected_prompt(p)):selected_prompt(p) for p in prompt_cache})
    save(dest/'report.json',report);save(dest/'phase_complete.json',report);return report


def selected_render_case(row,folder,processor,prompt):
    from renderer.main import render
    from RQs.RQ4_1.src.utils import foreground_support,isolated_glyph_tokens
    from .utils import save,RQ,HISTORY,digest
    base=ROOT/row['base'];sp=read(RQ/f"results/cpu_sp_v2/completed/{row['id']}.json")
    original=read(base/'processor_cpu.json');old=read(HISTORY/f"formal_v28/completed/{row['id']}__development__A_UNIFORM_E50__BASE.json")
    # Recompute unchanged P inputs once; all P arms share this PNG and mask.
    p=processor_audit(processor,base/'render/dashboard.png',prompt,original['image_tokens'],old['actual_retention']['indices'])
    if p['image_tokens']!=original['image_tokens'] or p['grid_thw']!=original['grid_thw']:raise ValueError('Historical processor geometry changed')
    if uniform_support_indices(read(base/'token_support.json'))['indices']!=old['actual_retention']['indices']:
        raise ValueError('Feature-free UNIFORM differs from historical committed mask')
    out={}
    for arm in ('S_JOINT','C_SOURCE_HASH'):
        dest=folder/arm;dest.mkdir(parents=True,exist_ok=True)
        evidence,design,prov=selected_dashboard(base,sp['selection'][arm]['cards'])
        save(dest/'evidence.json',evidence);save(dest/'design.json',design);save(dest/'provenance.json',prov)
        manifest=render(dest/'evidence.json',dest/'design.json',dest/'render')
        if manifest['status']!='passed':raise ValueError('Selected renderer qualification failed')
        exact_panel_pixels(base/'render/dashboard.png',dest/'render/dashboard.png',manifest['rectangles'])
        support=foreground_support(dest/'render',original['processed_pixels'],policy='shared_v2')
        if support['definite_empty_unanchored_roles'] or support['uncertain_empty_unanchored_roles']:
            # Use original already-qualified support for roles whose pixels,
            # positions and processor are byte-identical. Do not ignore empty
            # supports caused by a future representation change.
            historical=read(base/'token_support.json')
            resolved={}
            for rid in support['definite_empty_unanchored_roles']+support['uncertain_empty_unanchored_roles']:
                previous=historical['roles'][rid];free=sorted(set(previous['foreground_possible_tokens'])-set(support['anchors']))
                if previous['tokens'] and set(previous['tokens'])<=set(free):
                    support['roles'][rid]['tokens']=previous['tokens'];resolved[rid]='pixel_identical_previous_support'
                elif previous['foreground_possible_tokens'] and set(previous['foreground_possible_tokens'])<=set(support['anchors']):
                    support['roles'][rid]['fully_anchored']=True;resolved[rid]='all_previous_support_now_anchored'
                else:raise ValueError('Unresolved source support '+rid)
            support['historical_support_resolution']={'raw_definite':support['definite_empty_unanchored_roles'],
                'raw_uncertain':support['uncertain_empty_unanchored_roles'],'resolved':resolved}
            support['definite_empty_unanchored_roles']=[];support['uncertain_empty_unanchored_roles']=[]
        chosen=uniform_support_indices(support)
        if len(chosen['indices'])>len(old['actual_retention']['indices']):raise ValueError('S retained budget exceeded original K')
        save(dest/'token_support.json',support);save(dest/'retention.json',chosen)
        actual=processor_audit(processor,dest/'render/dashboard.png',selected_prompt(prompt),original['image_tokens'],chosen['indices'])
        if actual['processed_pixels']!=original['processed_pixels']:raise ValueError('S processor grid changed')
        save(dest/'processor.json',actual)
        out[arm]={'cards':len(evidence['cards']),'retained':len(chosen['indices']),'anchors':chosen['anchor_count'],
            'png_sha256':digest(dest/'render/dashboard.png'),'kept_pixels_equal':True,'processor':actual}
    return {'id':row['id'],'dataset':row['dataset'],'status':'completed','S':out,'P_processor':p,
        'original_K':len(old['actual_retention']['indices']),'new_model_calls':0,'full_cpu_qualified':False}


def pack_anchor_pixels(alpha,dom,compact_ties=False,accelerated=False):
    """Two deterministic coordinate-descent passes on actual anchor glyph ink.

    Shared/ambiguous block pixels remain fixed and cannot be credited as gains.
    This conservative prototype is always checked against a real renderer replay.
    """
    import numpy as np
    from collections import Counter
    alpha=np.asarray(alpha)>0;h,w=alpha.shape
    if w%32 or h%32:raise ValueError('Packing requires unresized merger-aligned canvas')
    owner=np.zeros((h,w),np.uint16);pieces=[];blocks=dom['blocks']
    bounds=[]
    for b in blocks:
        x,y,bw,bh=b['box'];x0=max(0,math.floor(x)-1);x1=min(w,math.ceil(x+bw)+1)
        y0=max(0,math.floor(y)-1);y1=min(h,math.ceil(y+bh)+1);bounds.append((x0,y0,x1,y1))
        owner[y0:y1,x0:x1]+=1
    def tokens(xs,ys,dx=0,dy=0):return np.unique(((ys+dy)//32)*(w//32)+(xs+dx)//32)
    fy,fx=np.nonzero(alpha&(owner!=1));fixed=tokens(fx,fy);counts=Counter(fixed.tolist())
    # Pixel ownership is unambiguous; account all fixed and movable supports.
    for b,bb in zip(blocks,bounds,strict=True):
        x0,y0,x1,y1=bb;yy,xx=np.nonzero(alpha[y0:y1,x0:x1]&(owner[y0:y1,x0:x1]==1))
        xs=xx+x0;ys=yy+y0;ts=tokens(xs,ys);counts.update(ts.tolist())
        pieces.append({'xs':xs,'ys':ys,'tokens':ts,'dx':0,'dy':0,
            'movable':not bool((alpha[y0:y1,x0:x1]&(owner[y0:y1,x0:x1]>1)).any())})
    before=len(counts);moves=[]
    def intersects(a,b):return a[0]<b[0]+b[2]-.01 and b[0]<a[0]+a[2]-.01 and a[1]<b[1]+b[3]-.01 and b[1]<a[1]+a[3]-.01
    current=[list(b['box']) for b in blocks]
    for sweep in range(2):
        for i,(b,p) in enumerate(zip(blocks,pieces,strict=True)):
            if not len(p['xs']) or not p['movable']:continue
            x,y,bw,bh=b['box'];px,py,pw,ph=b['panel']
            others=[(j,current[j]) for j in range(len(blocks)) if j!=i and blocks[j]['card']==b['card']]
            old=p['tokens'];old_set=set(old.tolist());base_count=len(counts)-sum(counts[int(t)]==1 for t in old)
            base_present={t for t,c in counts.items() if c>int(t in old_set)}
            best=(len(counts),len(old) if compact_ties else 0,abs(p['dx'])+abs(p['dy']),p['dx'],p['dy']);choice=None
            if accelerated:
                from .utils import best_packing_offset
                excluded=[ob for j,ob in others if not intersects(b['box'],blocks[j]['box'])]
                excluded += [ob for ob in b['obstacles'] if not intersects(b['box'],ob)]
                nearby=[ob for ob in excluded if intersects([x-16,y-16,bw+32,bh+32],ob)]
                occ=np.zeros((h//32)*(w//32),np.bool_);occ[list(base_present)]=True
                dx,dy=best_packing_offset(p['xs'],p['ys'],np.asarray(b['box'],np.float64),
                    np.asarray(b['panel'],np.float64),np.asarray(nearby,np.float64).reshape(-1,4),
                    occ,w//32,base_count,len(counts),len(old),p['dx'],p['dy'],compact_ties)
                if (dx,dy)!=(p['dx'],p['dy']):choice=(dx,dy,tokens(p['xs'],p['ys'],dx,dy))
            else:
                for dx in range(-16,17):
                    for dy in range(-16,17):
                        box=[x+dx,y+dy,bw,bh]
                        if box[0]<px or box[1]<py or box[0]+bw>px+pw or box[1]+bh>py+ph:continue
                        if any(intersects(box,ob) and not intersects(b['box'],blocks[j]['box']) for j,ob in others):continue
                        if any(intersects(box,ob) and not intersects(b['box'],ob) for ob in b['obstacles']):continue
                        candidate=tokens(p['xs'],p['ys'],dx,dy)
                        cost=base_count+sum(int(t) not in base_present for t in candidate)
                        rank=(cost,len(candidate) if compact_ties else 0,abs(dx)+abs(dy),dx,dy)
                        if rank<best:best=rank;choice=(dx,dy,candidate)
            if choice:
                dx,dy,ts=choice
                for t in old:
                    counts[int(t)]-=1
                    if not counts[int(t)]:del counts[int(t)]
                counts.update(ts.tolist());p.update(dx=dx,dy=dy,tokens=ts);current[i]=[x+dx,y+dy,bw,bh]
                moves.append({'sweep':sweep,'id':b['id'],'dx':dx,'dy':dy,'predicted_anchors':len(counts)})
    return {'offsets':[{'id':b['id'],'dx':p['dx'],'dy':p['dy']} for b,p in zip(blocks,pieces,strict=True) if p['dx'] or p['dy']],
        'before':before,'predicted_after':len(counts),'predicted_tokens':sorted(counts),'moves':moves,
        'search':'two_passes_integer_offsets_minus16_plus16','compact_ties':compact_ties,'conservative_shared_pixels_fixed':int((alpha&(owner>1)).sum())}


def pack_probe(row,base_render,dest,accelerated=False):
    import os,subprocess
    from PIL import Image
    from renderer.main import node_runtime,render
    from .utils import save,HISTORY
    from RQs.RQ4_1.src.utils import isolated_glyph_tokens
    dest.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,PLAYWRIGHT_BROWSERS_PATH=str(ROOT/'build/renderer_tooling/browsers'))
    subprocess.run([str(node_runtime()),str(ROOT/'src/renderer/web/dist/packAudit.mjs'),str(base_render)],env=env,check=True)
    dom=read(base_render/'packing_dom.json')
    compact_graphs={r['card'] for r in read(base_render/'geometry.json')['rectangles'] if r['component'] in {'graph.source_compact','graph.numeric_source'}}
    # A node with a role has two text lines. The whole node's browser box is
    # an obstacle for its neighbours; a label-only audit misses that boundary.
    evidence=read(base_render/'evidence.json')
    role_graphs={c['id'] for c in evidence['cards'] if c['id'] in compact_graphs and any(n.get('role') for n in c['data']['nodes'])}
    bindings=read(base_render/'manifest.json')['audit']['bindings']
    for block in dom['blocks']:
        if block['card'] in role_graphs:
            nodes=[b for b in bindings if b['card']==block['card'] and '.node.' in b['key']]
            block['obstacles'] += [[b['x'],b['y'],b['width'],b['height']] for b in nodes]
    save(base_render/'packing_dom_qualified.json',dom)
    with Image.open(base_render/'anchor_foreground.png') as image:packed=pack_anchor_pixels(image.getchannel('A'),dom,compact_ties=True,accelerated=accelerated)
    save(dest/'search.json',packed)
    design=read(base_render/'design.json');design['anchor_pack']={'schema':'AnchorPackV1','offsets':packed['offsets']}
    save(dest/'design.json',design)
    try:
        manifest=render(base_render/'evidence.json',dest/'design.json',dest/'render')
        actual=isolated_glyph_tokens(dest/'render/anchor_foreground.png',[manifest['width'],manifest['height']])
        repairs=[];final_render=dest/'render'
        # Withdraw only raster-ambiguous moves, never search a new offset after
        # seeing the replay. The exact actual raster remains the hard oracle.
        for repair in range(2):
            mismatch=set(actual)^set(packed['predicted_tokens'])
            if not mismatch:break
            gw=manifest['width']//32;cells=[(t%gw*32,t//gw*32,32,32) for t in mismatch]
            def overlap(a,b):return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]
            byid={b['id']:b for b in dom['blocks']};kept=[];withdrawn=[]
            for move in packed['offsets']:
                raw=byid[move['id']]['box']
                # Include the same one-pixel raster/antialias fringe as the
                # independent pixel-ownership extractor, not only DOM bounds.
                b=[math.floor(raw[0])-1,math.floor(raw[1])-1,math.ceil(raw[0]+raw[2])-math.floor(raw[0])+2,math.ceil(raw[1]+raw[3])-math.floor(raw[1])+2]
                shift=[b[0]+move['dx'],b[1]+move['dy'],b[2],b[3]]
                if any(overlap(b,c) or overlap(shift,c) for c in cells):withdrawn.append(move)
                else:kept.append(move)
            if not withdrawn:break
            with Image.open(base_render/'anchor_foreground.png') as im:predicted=predict_anchor_offsets(im.getchannel('A'),dom,kept)
            packed.update(offsets=kept,predicted_tokens=predicted)
            repairs.append({'withdrawn':withdrawn,'mismatch_tokens':sorted(mismatch)})
            design['anchor_pack']['offsets']=kept;save(dest/f'design_repair{repair+1}.json',design)
            final_render=dest/f'render_repair{repair+1}'
            manifest=render(base_render/'evidence.json',dest/f'design_repair{repair+1}.json',final_render)
            actual=isolated_glyph_tokens(final_render/'anchor_foreground.png',[manifest['width'],manifest['height']])
        save(dest/'accepted_search.json',packed)
        old=read(HISTORY/f"formal_v28/completed/{row['id']}__development__A_UNIFORM_E50__BASE.json")
        result={'id':row['id'],'dataset':row['dataset'],'render_status':manifest['status'],'actual_anchors':len(actual),
            'final_render':str(final_render.relative_to(ROOT)),'withdrawal_repairs':repairs,
            'original_K':len(old['actual_retention']['indices']),'before_anchors':packed['before'],
            'prediction_exact':actual==packed['predicted_tokens'],'moves':len(packed['offsets']),
            'anchor_cap_pass':len(actual)<=len(old['actual_retention']['indices']),
            'minimum_font_source':dom['min_font'],'full_cpu_qualified':False,'new_model_calls':0}
    except Exception as exc:result={'id':row['id'],'render_status':'failed','error':str(exc),'full_cpu_qualified':False}
    save(dest/'result.json',result);return result


def registered_request(row,arm,variant='BASE',request_index=None):
    """CPU-qualified public inputs only. Historical answer fields are excluded."""
    from .utils import RQ,HISTORY
    if arm=='X_SRP':
        if variant!='BASE':raise ValueError('Unregistered X_SRP measurement')
        return read(RQ/f"results/xsrp_v8/population02/inputs/{row['id']}/request.json")
    oid=row['id'];base=ROOT/row['base'];old=read(HISTORY/f'formal_v28/completed/{oid}__development__A_UNIFORM_E50__BASE.json')
    index=request_index if request_index is not None else read(HISTORY/'deployment_v26/request_index.json')['requests']
    request=index[oid+('__T_FULL__BASE' if arm=='T_FULL' else '__VISUAL__BASE')]
    image=ROOT/request['png'] if request.get('png') else None;prompt=request['prompt']
    groups=read(RQ/f'results/cpu_sp_v2/completed/{oid}.json')['groups'];retained=groups['retained']
    processor=read(RQ/f'results/cpu_render_v6/population01/completed/{oid}.json')['P_processor'];manifest=base/'render/manifest.json'
    operation=arm if arm.startswith('P_') or arm in {'C_LOCAL_FORWARD','C_SHAM_BI','C_GLOBAL_BI'} else 'U'
    if arm in {'S_JOINT','C_SOURCE_HASH','X_SP'}:
        chosen='S_JOINT' if arm=='X_SP' else arm
        folder=RQ/f'results/cpu_render_v6/population01/inputs/{oid}/{chosen}'
        image=folder/'render/dashboard.png';manifest=folder/'render/manifest.json'
        retained=read(folder/'retention.json')['indices'];prompt=selected_prompt(prompt)
        processor=read(RQ/f'results/cpu_render_v6/followup01/inputs/{oid}/{chosen}/processor.json')
        groups=read(RQ/f'results/cpu_render_v6/followup01/inputs/{oid}/X_SP/groups.json') if arm=='X_SP' else {}
        if arm=='X_SP':operation='P_LOCAL_BI'
    if variant=='QA':
        folder=RQ/f'results/cpu_qa_v7/population02/inputs/{oid}'
        if not folder.exists():folder=RQ/f'results/cpu_qa_v7/smoke_inputs/{oid}'
        prompt=read(folder/'prompt.json')['prompt'];image=folder/'render/dashboard.png';manifest=folder/'render/manifest.json'
        retained=read(folder/'retention.json')['indices'];groups=read(folder/'groups.json');processor=read(folder/'processor.json')
    if arm=='T_FULL':
        retained=[];groups={};manifest=None;operation='TEXT';processor={'text_tokens':request['input_tokens'],'image_tokens':0,'retained_input_tokens':request['input_tokens']}
    seed=old['decoder_seed']
    if variant in {'QA','REPEAT','TIMING'}:seed=int(stable(['rq43-seed-v1',oid,variant])[:8],16)%2147483647
    return {'prompt':prompt,'image':str(image.relative_to(ROOT)) if image else None,'retained':retained,'groups':groups,
        'operation':operation,'order':variant=='ORDER','seed':seed,'task':'QA' if variant=='QA' else 'RCA','attention':False,
        'manifest':str(manifest.relative_to(ROOT)) if manifest else None,'processor':processor}


def build_queue():
    from .utils import RQ,HISTORY,roster,save,model_identity,generation_identity
    config=read(RQ/'configs/execution_v7.json');rows=sorted(roster(),key=lambda r:stable(['rq43-formal-v1',r['id']]))
    model=model_identity();fingerprint=stable(model);items=[];owners={};mechanism=mechanism_rows();byid={r['id']:r for r in rows}
    request_index=read(HISTORY/'deployment_v26/request_index.json')['requests']
    matrix=[]
    for i,r in enumerate(rows):
        arms=config['arms'];arms=arms[i%len(arms):]+arms[:i%len(arms)]
        matrix.extend((r,a,'BASE') for a in arms)
    for r in mechanism:
        matrix.extend((r,a,'QA') for a in config['qa_arms'])
        matrix.extend((r,a,v) for v in ('ORDER','REPEAT') for a in ('U','P_LOCAL_BI'))
    for ds in ('aiops2022','aiops2025','aegislab'):
        matrix.extend((r,'T_FULL','TIMING') for r in [x for x in mechanism if x['dataset']==ds][:4])
    for r,a,v in matrix:
        req=registered_request(r,a,v,request_index);identity=generation_identity(req,fingerprint);req['identity']=identity
        key=f"{r['id']}__{a}__{v}";path=RQ/'results/deployment_v7/requests'/(key+'.json');save(path,req)
        item={'key':key,'id':r['id'],'dataset':r['dataset'],'event_group':r['event_group'],'arm':a,'variant':v,
            'task':req['task'],'identity':identity,'request':str(path.relative_to(ROOT)),'request_sha256':__import__('hashlib').sha256(path.read_bytes()).hexdigest(),
            'reference':None if v=='REPEAT' else owners.get(identity)}
        if v!='REPEAT':owners.setdefault(identity,key)
        items.append(item)
    # Hash interleave while references always follow their owner, never use results.
    pending=sorted(items,key=lambda x:stable(['rq43-queue-v1',x['key']]));ordered=[];seen=set()
    while pending:
        batch=[x for x in pending if not x['reference'] or x['reference'] in seen]
        if not batch:raise ValueError('Reference cycle')
        for x in batch:ordered.append(x);seen.add(x['key'])
        pending=[x for x in pending if x['key'] not in seen]
    if len(ordered)!=2412:raise ValueError('Registered position count differs')
    result={'schema':'RQ43FrozenQueueV7','items':ordered,'positions':len(ordered),'unique_calls':sum(not x['reference'] for x in ordered),
        'model':model,'model_fingerprint':fingerprint,'cancelled':config['cancelled'],'preselected_status':config['preselected_status'],
        'formal_attempt_cap':2646,'smoke_cap':18,'combined_cap':2664,'historical_baseline_new_calls':0}
    save(RQ/'results/deployment_v7/queue.json',result);return result


def materialize_frozen_visual(item,request,dest,processor):
    """Admit the exact qualified input, without repeating layout/packing search."""
    from .utils import queue_path,generation_identity,save
    if generation_identity(request,read(queue_path())['model_fingerprint'])!=item['identity']:
        raise ValueError('Qualified visual input was modified')
    manifest=read(ROOT/request['manifest'])
    if manifest.get('status')!='passed':raise ValueError('Qualified visual manifest is not passed')
    actual=processor_audit(processor,ROOT/request['image'],request['prompt'],
                           request['processor']['image_tokens'],request['retained'])
    if any(actual[k]!=request['processor'].get(k) for k in actual):
        raise ValueError('Qualified visual actual processor mismatch')
    request=dict(request,identity=item['identity']);save(dest/'request.json',request)
    return request


def cold_materialize(item,dest,processor):
    """Continuous public-package read, compile, render, mask, answer validation.

    No cross-call case cache. Existing frozen semantic records are the public
    input boundary, not raw telemetry ingestion; that boundary is reported.
    """
    from .utils import RQ,roster,save,generation_identity
    from renderer.main import render
    from RQs.RQ4_1.src.utils import foreground_support
    from RQs.RQ4_1.src.exps import ledger
    row=next(r for r in roster() if r['id']==item['id']);base=ROOT/row['base']
    public=read(ROOT/f"RQs/RQ3_21/preparation/compact_entity_v1/public/{row['id']}.json");packet=ledger(public)
    if packet['source_hash']!=read(base/'source_audit.json')['source_hash']:raise ValueError('Public fact identity mismatch')
    expected=read(ROOT/item['request']);req=dict(expected);arm=item['arm'];variant=item['variant']
    if arm in (*RESTORED_ARMS,'X_SRP'):
        # Explicitly authorized immutable runtime cache. No earlier model answer
        # is used to construct an input; no change to the one-call RCA method.
        return materialize_frozen_visual(item,req,dest,processor)
    if arm in {'T_FULL','HTML_SEMANTIC','HTML_PLOT_CODE'}:
        save(dest/'request.json',req);return req
    if variant=='QA':
        qa_case(row,dest,processor)
        req.update(image=str((dest/'render/dashboard.png').relative_to(ROOT)),manifest=str((dest/'render/manifest.json').relative_to(ROOT)),
            prompt=read(dest/'prompt.json')['prompt'],retained=read(dest/'retention.json')['indices'],groups=read(dest/'groups.json'),processor=read(dest/'processor.json'))
    else:
        if arm in {'S_JOINT','C_SOURCE_HASH','X_SP'}:
            method='S_JOINT' if arm=='X_SP' else arm;selection=sp_case(row)['selection'][method]
            evidence,design,prov=selected_dashboard(base,selection['cards'])
        else:evidence=read(base/'evidence.json');design=read(base/'design.json');prov=read(base/'provenance.json')
        save(dest/'evidence.json',evidence);save(dest/'design.json',design);save(dest/'provenance.json',prov)
        manifest=render(dest/'evidence.json',dest/'design.json',dest/'render')
        if manifest['status']!='passed':raise ValueError('Cold render failed')
        original=read(base/'processor_cpu.json');support=foreground_support(dest/'render',original['processed_pixels'],policy='shared_v2')
        if support['definite_empty_unanchored_roles'] or support['uncertain_empty_unanchored_roles']:raise ValueError('Cold support unresolved')
        selected=uniform_support_indices(support);save(dest/'token_support.json',support)
        actual=processor_audit(processor,dest/'render/dashboard.png',req['prompt'],original['image_tokens'],selected['indices'])
        groups=source_token_groups(dict(row,base=str(dest.relative_to(ROOT))),packet,read(base/'mapping.json'),evidence,
            manifest['rectangles'],actual,selected['indices']) if req['groups'] else {}
        req.update(image=str((dest/'render/dashboard.png').relative_to(ROOT)),manifest=str((dest/'render/manifest.json').relative_to(ROOT)),
            retained=selected['indices'],groups=groups,processor=actual)
    from .utils import queue_path
    model=read(queue_path())['model_fingerprint']
    if generation_identity(req,model)!=item['identity']:raise ValueError('Cold computation differs from frozen request')
    req['identity']=item['identity'];save(dest/'request.json',req);return req


def vllm_grouped_delta(q,k,v,g,beta,groups,bidirectional=True):
    """Same registered branch for vLLM's already L2-normalized Q/K tensors."""
    import torch
    from transformers.models.qwen3_5.modeling_qwen3_5 import torch_chunk_gated_delta_rule
    if v.shape[2]%q.shape[2] or q.shape[2]!=k.shape[2]:raise ValueError('Invalid grouped-value attention heads')
    repeat=v.shape[2]//q.shape[2]
    if repeat!=1:q=q.repeat_interleave(repeat,dim=2);k=k.repeat_interleave(repeat,dim=2)
    result=torch.zeros_like(v);buckets=defaultdict(list)
    for group in groups:buckets[math.ceil(len(group)/64)*64].append(group)
    for length,items in buckets.items():
        directions=[group for group in items]+([list(reversed(group)) for group in items] if bidirectional else [])
        packed=[]
        for tensor in (q,k,v,g,beta):
            batch=tensor.new_zeros((len(directions),length,*tensor.shape[2:]))
            for row,positions in enumerate(directions):batch[row,:len(positions)]=tensor[0,positions]
            packed.append(batch)
        out,_=torch_chunk_gated_delta_rule(*packed[:3],g=packed[3],beta=packed[4],
            initial_state=None,output_final_state=False,use_qk_l2norm_in_kernel=False)
        for row,positions in enumerate(directions):result[0,positions]+=out[row,:len(positions)]/(2 if bidirectional else 1)
    return result


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
        for index in range(3):
            chunk=layers[index].linear_attn.chunk_gated_delta_rule;native=chunk.forward
            def mixed(*args,_native=native,_index=index,**kwargs):
                out,final_state=_native(*args,**kwargs)
                records=[r for r in state['records'] if r['prefill']]
                if not records:return out,final_state
                if args:raise ValueError('Unexpected positional vLLM chunk arguments')
                if kwargs.get('use_qk_l2norm_in_kernel') is not False:raise ValueError('Expected pre-normalized vLLM Q/K')
                q,k,v,g,beta=(kwargs[x] for x in ('q','k','v','g','beta'))
                if sum(r['end']-r['start'] for r in records)!=q.shape[1]:raise ValueError('Prefill pack boundary mismatch')
                offset=0
                for rec in records:
                    meta=rec['meta'];n=rec['end']-rec['start'];mode=meta['operation'];groups=meta['groups']
                    if mode=='C_GLOBAL_BI':groups=[sorted(i for group in groups for i in group)] if groups else []
                    if mode not in {'U','P_SOFT_IMAGE'} and groups:
                        sl=slice(offset,offset+n)
                        aux=vllm_grouped_delta(q[:,sl],k[:,sl],v[:,sl],g[:,sl],beta[:,sl],groups,mode!='C_LOCAL_FORWARD')
                        ids=sorted(i for group in groups for i in group);global_ids=[i+offset for i in ids]
                        out[:,global_ids]=.75*out[:,global_ids]+.25*aux[:,ids]
                        state['requests'][rec['key']]['branch_calls']+=1
                    offset+=n
                return out,final_state
            chunk.forward=mixed
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
                if rec['prefill'] and meta['operation'] in {'P_SOFT_IMAGE','P_DUAL'}:
                    vv=v[sl].view(-1,module.num_kv_heads,module.head_dim).transpose(0,1)[None]
                    image=list(range(meta['image_start'],meta['image_start']+meta['image_count']))
                    keys=list(range(meta['image_start']))+image;repeat=module.num_heads//module.num_kv_heads
                    aux=F.scaled_dot_product_attention(qq[:,:,image],kk[:,:,keys].repeat_interleave(repeat,dim=1),
                        vv[:,:,keys].repeat_interleave(repeat,dim=1),dropout_p=0.,is_causal=False,scale=module.head_dim**-.5)
                    indexes=[rec['start']+i for i in image]
                    attn[indexes]=.75*attn[indexes]+.25*aux[0].transpose(0,1).reshape(len(image),-1)
                    entry['branch_calls']+=1
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
        self.processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
        eos=read('/home/lglsj/CanvasRCA/models/Qwen3.8-27B/generation_config.json')['eos_token_id']
        self.stop_token_ids=sorted(set(eos if isinstance(eos,list) else [eos]))
        import xgrammar as xgr
        from .utils import rca_schema
        self.rca_grammar=str(xgr.Grammar.from_json_schema(rca_schema(True),any_whitespace=False))
        self.loop=asyncio.new_event_loop();self.ready=concurrent.futures.Future()
        self.thread=threading.Thread(target=self._serve,name='rq43-vllm-control',daemon=True);self.thread.start()
        self.warmup=self.ready.result(timeout=900)
    def _serve(self):
        import asyncio
        asyncio.set_event_loop(self.loop)
        async def start():
            import time
            from vllm.engine.arg_utils import AsyncEngineArgs
            from vllm.v1.engine.async_llm import AsyncLLM
            from .utils import RQ,VLLMCacheAdmission
            cfg=read(RQ/'configs/execution_v13.json');began=time.monotonic()
            self.engine=AsyncLLM.from_engine_args(AsyncEngineArgs(**cfg['engine']),start_engine_loop=True)
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
            grammar=StructuredOutputsParams(grammar=self.rca_grammar) if request['task']=='RCA' else StructuredOutputsParams(json_object=True)
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
                'image_tokens_retained':len(request['retained']),'cache_lengths':[n],'branch_calls':audit['branch_calls'],
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


class LocalSolver:
    """Frozen local HF solver. No case facts outside the image enter generation."""
    def __init__(self,scope,attention_folder,deadline=None,shared=None,slot=None,prefill_gate=None,forward_gate=None,prefill_stream=None):
        from .gates import require_execution
        require_execution(scope)
        import torch,xgrammar as xgr
        from transformers import AutoProcessor,Qwen3_5ForConditionalGeneration
        from vlmrca.vlm.passive_summary import AttentionStore,PassiveAttentionTap
        from .utils import rca_schema
        torch.set_num_threads(1 if slot is not None else 8);torch.cuda.set_per_process_memory_fraction(.75)
        if scope=='smoke':gpu_operator_probe()
        from .utils import accelerator_identity
        self.accelerator=accelerator_identity(verify=shared is None)
        self.torch=torch;path='/home/lglsj/CanvasRCA/models/Qwen3.8-27B'
        self.processor=AutoProcessor.from_pretrained(path,local_files_only=True)
        from .utils import shared_weight_model,install_independent_tap
        self.concurrent=slot is not None;self.prefill_gate=prefill_gate;self.prefill_held=False;self.forward_gate=forward_gate
        self.prefill_stream=prefill_stream
        self.model=(shared_weight_model(shared.pristine) if shared is not None else
            Qwen3_5ForConditionalGeneration.from_pretrained(path,dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True).to('cuda').eval())
        if self.concurrent and shared is None:self.pristine=shared_weight_model(self.model)
        from .utils import RQ,install_compiled_normalizers
        self.normalizer_counts=install_compiled_normalizers(self.model) if read(RQ/'configs/execution_v9.json').get('compiled_norms') else {}
        if self.accelerator:
            from transformers.models.qwen3_5.modeling_qwen3_5 import is_fast_path_available
            if not is_fast_path_available:raise RuntimeError('Registered linear-attention fast kernels unavailable')
            linear=[m for m in self.model.modules() if hasattr(m,'chunk_gated_delta_rule')]
            if len(linear)!=48 or any(not m.chunk_gated_delta_rule.__module__.startswith('fla.') for m in linear):
                raise RuntimeError('All 48 linear attention layers must use the frozen FLA implementation')
        if self.concurrent:
            from .utils import install_reserved_cache
            self.cache_capacity=40960 if slot==0 else 16384
            self.reserved_cache=install_reserved_cache(self.model,self.cache_capacity,'cuda',torch.bfloat16)
            # Serialize Python kernel dispatch, not whole generations. Independent
            # CUDA streams/caches still overlap; avoid eight Python threads
            # fighting over the GIL for every one of the 64 decoder blocks.
            native_forward=self.model.forward
            from functools import wraps
            @wraps(native_forward)
            def forward(*args,**kwargs):
                with forward_gate:
                    if not self.prefill_held:return native_forward(*args,**kwargs)
                    # All large prompt workspaces share one allocator stream.
                    # Wait for packed inputs, then hand logits back to the slot.
                    self.prefill_stream.wait_stream(self.stream)
                    with torch.cuda.stream(self.prefill_stream):result=native_forward(*args,**kwargs)
                    self.stream.wait_stream(self.prefill_stream)
                    result.logits.record_stream(self.stream)
                    return result
            self.model.forward=forward
        compiler=xgr.GrammarCompiler(xgr.TokenizerInfo.from_huggingface(self.processor.tokenizer,vocab_size=self.model.config.text_config.vocab_size))
        self.grammar=compiler.compile_json_schema(rca_schema(True),any_whitespace=False);self.qa_grammar=compiler.compile_builtin_json_grammar()
        self.store=AttentionStore(attention_folder);self.tap=PassiveAttentionTap(self.store)
        if self.concurrent:install_independent_tap(self.tap,self.model,slot)
        else:self.tap.install(self.model)
        self.stream=torch.cuda.Stream() if self.concurrent else None
        if self.stream is not None:self.stream.wait_stream(torch.cuda.current_stream())
        self.deadline=deadline;self.last_usage=None;self.call_ordinal=0
    def __call__(self,request):
        if not self.concurrent:return self._generate(request)
        with self.torch.cuda.stream(self.stream):
            self.host_thread_started=__import__('time').thread_time()
            self.admitted_monotonic=__import__('time').monotonic();self.prefill_done_monotonic=None
            self.prefill_gate.acquire();self.prefill_held=True
            try:
                # Reuse warmed allocator segments. No global barrier or allocator
                # flush at a request boundary; other slots may keep decoding.
                self.prefill_reclaimed_bytes=0;self.prefill_reclaim_seconds=0.
                return self._generate(request)
            finally:
                self.stream.synchronize()
                if self.prefill_held:self.prefill_held=False;self.prefill_gate.release()

    def _generate(self,request):
        import time
        from contextlib import nullcontext
        from PIL import Image
        from transformers import LogitsProcessorList,StoppingCriteriaList,StoppingCriteria
        from xgrammar.contrib.hf import LogitsProcessor
        from vlmrca.vlm.passive_summary import RankingPrefixGreedy
        from RQs.RQ4_1.src.utils import pack_injected_batch,injected_generate,attention_key_regions
        torch=self.torch;began=time.monotonic();self.call_ordinal+=1;self.decode_steps=0
        if self.deadline is not None and began>=self.deadline:raise TimeoutError('Shared smoke deadline reached')
        if request['image']:
            with Image.open(ROOT/request['image']) as image:batch=self.processor(text=[request['prompt']],images=[image.convert('RGB')],return_tensors='pt')
        else:batch=self.processor(text=[request['prompt']],return_tensors='pt')
        count=int(batch['input_ids'].shape[1]);actual_image=int((batch['input_ids']==self.model.config.image_token_id).sum())
        batch={k:v.to('cuda') for k,v in batch.items()}
        if not self.concurrent:torch.manual_seed(request['seed'])
        self.model.model.rope_deltas=None
        processors=[LogitsProcessor(self.grammar if request['task']=='RCA' else self.qa_grammar)]
        if request['task']=='RCA':processors.append(RankingPrefixGreedy(self.processor.tokenizer))
        deadline=self.deadline
        class Stop(StoppingCriteria):
            def __call__(self,input_ids,scores,**kwargs):return deadline is not None and time.monotonic()>=deadline
        options={'max_new_tokens':8192,'do_sample':True,'temperature':1.,'top_p':.95,'top_k':0,
            'logits_processor':LogitsProcessorList(processors),'stopping_criteria':StoppingCriteriaList([Stop()])}
        if self.concurrent:
            from .utils import IsolatedSampler
            options['logits_processor'].append(IsolatedSampler(request['seed'],'cuda'))
            options['top_p']=1. # top-p .95 is applied once by IsolatedSampler.
        sync=self.stream.synchronize if self.concurrent else torch.cuda.synchronize
        adapter=None;start=None;packed=None;features=None;phases={};cache_lengths=[]
        def cache_hook(module,args,kwargs,output):
            self.decode_steps+=1
            cache=getattr(output,'past_key_values',None)
            if cache is not None and len(cache_lengths)<3:cache_lengths.append(int(cache.get_seq_length()))
            if self.concurrent and self.prefill_held:
                self.stream.synchronize();self.prefill_done_monotonic=time.monotonic()
                self.prefill_held=False;self.prefill_gate.release()
        hook=self.model.register_forward_hook(cache_hook,with_kwargs=True)
        try:
            with torch.inference_mode():
                if request['image']:
                    tick=time.monotonic()
                    if self.concurrent:self.prefill_stream.wait_stream(self.stream)
                    with torch.cuda.stream(self.prefill_stream) if self.concurrent else nullcontext():
                        enc=self.model.model.get_image_features(batch['pixel_values'],batch['image_grid_thw'],return_dict=True)
                    if self.concurrent:
                        self.stream.wait_stream(self.prefill_stream)
                        for feature in enc.pooler_output:feature.record_stream(self.stream)
                    features=list(enc.pooler_output);del enc;sync();phases['vision_seconds']=time.monotonic()-tick
                    positions,_=self.model.model.get_rope_index(batch['input_ids'],attention_mask=batch['attention_mask'],image_grid_thw=batch['image_grid_thw'],mm_token_type_ids=batch['mm_token_type_ids'])
                    packed=pack_injected_batch(batch['input_ids'],batch['attention_mask'],positions,self.model.get_input_embeddings()(batch['input_ids']),features,
                        self.model.config.image_token_id,[request['retained']])
                    start=int((batch['input_ids'][0]==self.model.config.image_token_id).nonzero()[0]);count=packed['inputs_embeds'].shape[1]
                    groups=language_groups(request['groups'],start,sham=request['operation']=='C_SHAM_BI') if request['groups'] else []
                    if request['order']:
                        packed['inputs_embeds'],packed['position_ids'],packed['rope_deltas']=reorder_visual_prefix(packed['inputs_embeds'],packed['position_ids'],request['groups'],start,packed['rope_deltas'])
                        # Source membership follows the moved token, not its old slot.
                        mapping={b:a for a,b in request['groups']['order_token_source_by_slot']};rank={v:i for i,v in enumerate(request['retained'])}
                        groups=[[start+rank[mapping.get(v,v)] for v in g] for g in request['groups']['groups'].values()]
                        groups=[sorted(g) for g in groups]
                    if request['operation']!='U':adapter=VisualPrefillAdapter(self.model,groups,list(range(start,start+len(request['retained']))),request['operation'])
                    if request['attention']:
                        grid=batch['image_grid_thw'][0].tolist();attention=attention_key_regions(read(ROOT/request['manifest']),(grid[1]//2,grid[2]//2),
                            batch['input_ids'][0].cpu().numpy(),self.model.config.image_token_id,request['retained'])
                        ids=attention['key_region']+1
                        if request['order']:
                            rank={v:start+i for i,v in enumerate(request['retained'])};old=ids.copy()
                            for a,b in request['groups']['order_token_source_by_slot']:ids[rank[a]]=old[rank[b]]
                        attention_key=stable([request['identity'],self.call_ordinal]) if self.concurrent else request['identity']
                        self.tap.begin(attention_key,torch.tensor(ids,device='cuda',dtype=torch.long),['other:generated']+attention['regions'],stable(ids.tolist()))
                if count+8192>40960:raise ValueError('Runtime context overflow')
                if self.concurrent and count+8192>self.cache_capacity:raise ValueError('Actual input exceeds selected reserved slot')
                sync();tick=time.monotonic()
                if request['image']:
                    with adapter.prefill() if adapter else nullcontext():
                        output=injected_generate(self.model,batch,features,[request['retained']],options,prepared=packed)
                else:
                    output=self.model.generate(**batch,use_cache=True,**options)[:,count:]
                sync();phases['language_seconds']=time.monotonic()-tick
            if self.deadline is not None and time.monotonic()>=self.deadline:raise TimeoutError('Incomplete smoke generation at deadline')
            tokens=output[0];response=self.processor.tokenizer.decode(tokens,skip_special_tokens=True)
            branches=adapter.branch_calls if adapter else 0
            expected={'P_LOCAL_BI':3,'P_SOFT_IMAGE':1,'P_DUAL':4,'C_LOCAL_FORWARD':3,'C_SHAM_BI':3,'C_GLOBAL_BI':3}.get(request['operation'],0)
            if branches!=expected:raise ValueError(f'Prefill operation did not execute exactly once: {branches} vs {expected}')
            if not cache_lengths or cache_lengths[0]!=count:raise ValueError('Actual cache prefix differs from retained request')
            self.last_usage={'input_tokens':count,'output_tokens':int(tokens.numel()),'image_tokens_original':actual_image,
                'image_tokens_retained':len(request['retained']),'processor_model_seconds':time.monotonic()-began,**phases,
                'branch_calls':branches,'cache_lengths':cache_lengths,'attention_requested':request['attention'],
                'attention_error':self.tap.error,'attention_missed':self.tap.missed,'stop_reason':'length' if tokens.numel()==8192 else 'eos',
                'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'accelerator':self.accelerator,
                'compiled_normalizers':self.normalizer_counts,
                'implementation_generation_identity':stable([request['identity'],self.accelerator,self.normalizer_counts,'fixed_backing_live_prefix_v12' if self.concurrent else 'dynamic'])}
            if self.concurrent:self.last_usage.update(runtime_revision='concurrency_v12',request_concurrency=8,
                cache_policy='fixed_backing_live_prefix',cache_capacity=self.cache_capacity,
                reserved_cache_bytes=self.reserved_cache.reserved_bytes,
                gpu_batch_per_request=1,peak_allocated_scope='whole_process',sampling_rng='independent_per_request',
                admitted_monotonic=self.admitted_monotonic,prefill_done_monotonic=self.prefill_done_monotonic,
                finished_monotonic=time.monotonic(),prefill_reclaimed_bytes=self.prefill_reclaimed_bytes,
                prefill_reclaim_seconds=self.prefill_reclaim_seconds,
                host_thread_cpu_seconds=time.thread_time()-self.host_thread_started,
                host_affinity=sorted(__import__('os').sched_getaffinity(0)),
                torch_intraop_threads=torch.get_num_threads())
            if request['attention']:self.last_usage['attention_record_key']=attention_key
            return response
        finally:
            hook.remove();self.tap.end()
            if adapter:adapter.close()
    def close(self):
        self.tap.close();self.store.close();del self.model
        if hasattr(self,'reserved_cache'):del self.reserved_cache
        if hasattr(self,'pristine'):del self.pristine
        self.torch.cuda.empty_cache()


def execution_loop(scope):
    """Qualified single-owner queue; power loss never loses committed answers."""
    import os,signal,time,traceback,fcntl
    from .utils import RQ,save,RuntimeSession,score_context,digest,deduplicate_cold_files,queue_path
    from .gates import require_execution,validate_request,execution_fingerprint
    from .utils import execution_folder
    if execution_folder(scope).name in {'deployment_v9','deployment_v11','deployment_v12','deployment_v13','deployment_v15','deployment_v16','deployment_v17'}:return concurrent_execution(scope)
    require_execution(scope)
    root=RQ/('results/gpu_smoke_v7' if scope=='smoke' else 'results/formal_v7');root.mkdir(parents=True,exist_ok=True)
    queue=read(queue_path(scope))
    if (root/'phase_complete.json').exists():return read(root/'phase_complete.json')
    if (root/'BLOCKED.json').exists():raise RuntimeError('Known error requires repair; no automatic correctness retry')
    owner=(RQ/'results/deployment_v7/gpu_owner.lock').open('a');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    session=RuntimeSession(root/'execution',limit=18 if scope=='smoke' else 2646);solver=None;handlers={}
    items=queue['items'];deadline=None
    if scope=='smoke':
        clock=root/'clock.json'
        if not clock.exists():save(clock,{'started_unix':time.time(),'seconds':600})
        remaining=600-(time.time()-read(clock)['started_unix'])
        if remaining<=0:session.close();owner.close();raise TimeoutError('Original logical smoke deadline exhausted')
        deadline=time.monotonic()+remaining
    def progress(state,current=None):
        count=len(list((session.root/'completed').glob('*.json')))
        save(root/'progress.json',{'status':state,'completed':count,'total':len(items),'current':current,
            'pid':os.getpid(),'updated':time.time(),'calls':session.calls.summary()})
    def pause(sig,frame):save(session.root/'PAUSE',{'signal':sig,'time':time.time()})
    for sig in (signal.SIGINT,signal.SIGTERM):handlers[sig]=signal.signal(sig,pause)
    try:
        save(root/'owner.json',{'pid':os.getpid(),'boot_id':__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
        save(root/'recovery'/str(time.time_ns()),session.recover())
        if (session.root/'PAUSE').exists():progress('paused');return
        for item in items:
            done=session.completed(item['key'])
            if done:
                if done['request_hash']!=item['identity']:raise ValueError('Committed queue identity mismatch')
                continue
            if (session.root/'PAUSE').exists():break
            states=session.calls.latest_states()
            if not item.get('reference') and states.get(item['key'])!='complete' and solver is None:
                progress('model_loading',item['key']);solver=LocalSolver(scope,root/'attention'/str(time.time_ns()),deadline);session.provider=solver
            progress('running',item['key'])
            def materialize(entry,dest):
                req=cold_materialize(entry,dest,solver.processor)
                if scope=='smoke':req['attention']=entry.get('attention',False)
                else:
                    admitted=read(RQ/'results/gpu_smoke_v7/report.json').get('attention_enabled',False)
                    req['attention']=admitted and entry['id'] in {r['id'] for r in mechanism_rows()} and entry['arm'] in {'U','P_LOCAL_BI','C_GLOBAL_BI'}
                return req
            result=session.run(item,materialize,score_context,validate_request)
            if result.get('status')=='paused':break
            print('COMMITTED',item['key'],result['outcome']['status'],result['usage']['input_tokens'],result['usage']['output_tokens'],flush=True)
            # Storage optimization happens only after the measured call commits.
            req=read(session.root/result['request_path'])
            if req['image']:
                folder=(ROOT/req['image']).parent.parent;reference=read(ROOT/item['request'])
                qualified=(ROOT/reference['image']).parent.parent
                deduplicate_cold_files(folder,qualified)
            progress('running')
        progress('draining')
        if solver:
            closing=solver;solver=None;closing.close()
        records=[session.completed(item['key']) for item in items]
        if any(r is None for r in records):progress('paused');return
        if scope=='smoke':
            off,on=records[:2];ratio=on['usage']['processor_model_seconds']/off['usage']['processor_model_seconds']
            attention_ok=ratio<=1.05 and off['response']==on['response'] and not on['usage']['attention_error'] and on['usage']['attention_missed']==0
            files=list((root/'attention').rglob('*.json'));sizes=[p.stat().st_size for p in files]
            from vlmrca.vlm.passive_summary import AttentionStore
            attention_ok=attention_ok and bool(sizes) and max(sizes)<=65536 and AttentionStore.storage_ceiling()<=1_000_000_000
            report={'status':'passed','scope':'all_surviving_unique_execution_branches','positions':len(records),'calls':session.calls.summary(),
                'execution_fingerprint':execution_fingerprint(),'attention_enabled':bool(attention_ok),'attention_time_ratio':ratio,
                'attention_record_sizes':sizes,'attention_projected_upper_bytes':AttentionStore.storage_ceiling(),
                'elapsed_seconds':time.time()-read(root/'clock.json')['started_unix'],
                'model_failures':sum(r['outcome']['status']=='model_failure' for r in records),
                'correctness_is_not_a_gate':True,'full_matrix_per_dataset_gpu_coverage':False}
            if report['elapsed_seconds']>600:raise TimeoutError('Smoke save/verification deadline exceeded')
            save(root/'report.json',report)
        phase={'status':'complete','positions':len(records),'calls':session.calls.summary(),'queue_sha256':digest(queue_path(scope)),
            'writers_drained':True,'execution_fingerprint':execution_fingerprint()}
        save(root/'phase_complete.json',phase);progress('complete');return phase
    except BaseException as exc:
        with session.calls.connect() as db:pending=db.execute("SELECT id FROM calls WHERE state='started'").fetchall()
        for (attempt,) in pending:session.calls.finish(attempt,{'error':repr(exc)},'infrastructure_failure')
        record={'status':'failed','error':repr(exc),'traceback':traceback.format_exc(),'time':time.time(),'execution_fingerprint':execution_fingerprint()}
        save(root/'BLOCKED.json',record)
        if scope=='smoke':save(root/'report.json',record)
        progress('blocked');raise
    finally:
        try:
            if solver:solver.close()
        finally:
            session.close();owner.close()
            for sig,handler in handlers.items():signal.signal(sig,handler)


class ConcurrentSolvers:
    """Eight independent request states and streams, one shared parameter store."""
    def __init__(self,scope,folder,deadline=None):
        from .gates import require_execution
        require_execution(scope)
        import threading
        from .utils import CapacitySlots
        self.free=CapacitySlots([40960]+[16384]*7);self.local=threading.local();self.solvers=[]
        import torch
        gate=threading.Semaphore(1);forward_gate=threading.Lock();prefill_stream=torch.cuda.Stream()
        try:
            for slot in range(8):
                solver=LocalSolver(scope,folder/f'slot{slot}',deadline,
                    shared=self.solvers[0] if self.solvers else None,slot=slot,prefill_gate=gate,forward_gate=forward_gate,prefill_stream=prefill_stream)
                self.solvers.append(solver)
            self.warmup=self.warm()
        except BaseException:
            self.close();raise
    @property
    def last_usage(self):return self.local.usage
    def __call__(self,request):
        needed=request['processor']['text_tokens']+len(request['retained'])+8192
        slot=self.free.acquire(needed)
        try:
            solver=self.solvers[slot];response=solver(request)
            self.local.usage={**solver.last_usage,'gpu_slot':slot};return response
        finally:self.free.release(slot)
    def warm(self):
        """Identical initialization in smoke/formal; no generation or extra calls."""
        import time
        torch=self.solvers[0].torch;began=time.monotonic();seen=set()
        with torch.inference_mode():
            for m in self.solvers[0].model.modules():
                if type(m).__name__ not in {'Qwen3_5RMSNorm','FusedRMSNormGated'}:continue
                key=(type(m).__name__,m.weight.numel())
                if key in seen:continue
                seen.add(key)
                for length in (1,129):
                    x=torch.zeros(length,m.weight.numel(),device='cuda',dtype=torch.bfloat16)
                    if key[0]=='FusedRMSNormGated':m(x,x)
                    else:m(x)
            torch.cuda.synchronize()
        return {'status':'initialized','seconds':time.monotonic()-began,'model_calls':0,
            'cache_capacities':list(self.free.capacities),'cache_bytes':sum(s.reserved_cache.reserved_bytes for s in self.solvers),
            'memory_allocated_bytes':torch.cuda.memory_allocated(),'memory_reserved_bytes':torch.cuda.memory_reserved(),
            'norm_signatures':sorted(seen),'scope':'shared initialization; not a GPU qualification test'}
    def close(self):
        errors=[]
        for solver in reversed(self.solvers):
            try:solver.close()
            except Exception as exc:errors.append(repr(exc))
        self.solvers.clear()
        if errors:raise RuntimeError('Concurrent solver shutdown: '+repr(errors))


def concurrent_execution(scope):
    """RAM-backed look-ahead: CPU keeps preparing independently of GPU backlog.

    At most eight process futures and eight GPU futures exist in RAM. Complete
    prepared requests live in tmpfs with byte accounting and safe backpressure.
    No model call starts during CPU preparation.
    """
    import os,time,signal,traceback,fcntl,multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor,wait,FIRST_COMPLETED
    from .utils import RQ,save,RuntimeSession,score_context,digest,queue_path,RamPreparationBuffer,runtime_cpu_partition,pin_all_host_threads,execution_folder
    from .gates import require_execution,validate_request,execution_fingerprint
    from .main import prepare_initializer,prepare_formal,prepare_restoration,restoration_summary
    require_execution(scope);smoke=scope=='concurrent_smoke'
    runtime_revision='vllm_v13' if scope=='formal' and execution_folder(scope).name in {'deployment_v13','deployment_v15','deployment_v16','deployment_v17'} else 'concurrency_v12'
    host_partition=runtime_cpu_partition(8)
    pin_all_host_threads(host_partition['gpu_host_cpus'])
    deployment=RQ/'results/deployment_v9'
    if smoke:
        registration=read(deployment/'active_smoke.json');root=ROOT/registration['root']
        path=deployment/'smoke_queue.json';limit=18
        clock=root/'clock.json'
        if not clock.exists():save(clock,{'started_unix':time.time(),'seconds':600})
        deadline=time.monotonic()+600-(time.time()-read(clock)['started_unix'])
    else:root=RQ/'results/formal_v7';path=queue_path();limit=read(path)['formal_attempt_cap'];deadline=None
    root.mkdir(parents=True,exist_ok=True);queue=read(path);items=queue['items']
    if (root/'phase_complete.json').exists():return read(root/'phase_complete.json')
    if (root/'BLOCKED.json').exists():raise RuntimeError('Known failure needs repair')
    owner=(RQ/'results/deployment_v7/gpu_owner.lock').open('a');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
    save(root/'host_partition.json',{**host_partition,'pid':os.getpid(),'process_group':os.getpgrp(),
        'OMP_NUM_THREADS':os.environ.get('OMP_NUM_THREADS'),'MKL_NUM_THREADS':os.environ.get('MKL_NUM_THREADS'),
        'OPENBLAS_NUM_THREADS':os.environ.get('OPENBLAS_NUM_THREADS'),'recorded_unix':time.time()})
    session=RuntimeSession(root/'execution',limit=limit);handlers={};provider=None;cpu_pool=None;gpu_pool=None;buffer=None
    preparing={};running={};prepared=set();errors=[];peak_cpu=0;peak_gpu=0;worker_pids=set();worker_cores=set()
    completed=set();launched=set();cursor=0;last_progress=0.;sources={r['id']:r for r in __import__('RQs.RQ4_3.src.utils',fromlist=['roster']).roster()}
    audit_registration=RQ/'results/cooperative_restoration.json';audit_folder=None;audit_pending=[];auditing={}
    if not smoke and audit_registration.exists() and read(audit_registration).get('enabled'):
        audit_folder=ROOT/read(audit_registration)['folder']
        audit_pending=[r for r in sources.values() if not (audit_folder/'completed'/(r['id']+'.json')).exists()]
        restoration_summary(audit_folder)
    metadata={};gpu_samples=[];boot=__import__('pathlib').Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    def pause(sig,frame):save(session.root/'PAUSE',{'signal':sig,'time':time.time()})
    def progress(state):
        if provider:
            import pynvml
            if not gpu_samples:pynvml.nvmlInit()
            handle=pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_samples.append({'t':time.monotonic(),'gpu_utilization':pynvml.nvmlDeviceGetUtilizationRates(handle).gpu,
                'memory_bytes':pynvml.nvmlDeviceGetMemoryInfo(handle).used,'inflight':len(running),
                'cpu_active':len(preparing),'prepared_in_RAM':len(metadata),'RAM_buffer_bytes':buffer.bytes if buffer else 0,
                'decode_steps_by_slot':[getattr(s,'decode_steps',0) for s in provider.solvers],
                'host_process_cpu_seconds':time.process_time()})
        save(root/'progress.json',{'status':state,'completed':len(completed),'total':len(items),'pid':os.getpid(),
            'updated':time.time(),'calls':session.calls.summary(),'cpu_workers':8,'gpu_concurrency':8,
            'cpu_active':len(preparing),'restoration_cpu_active':len(auditing),'restoration_cpu_pending':len(audit_pending),'gpu_inflight':len(running),'prepared_in_RAM':len(metadata),
            'RAM_buffer_bytes':buffer.bytes if buffer else 0,'RAM_buffer_limit_bytes':buffer.capacity if buffer else 0,
            'decode_steps_by_slot':[getattr(s,'decode_steps',0) for s in provider.solvers] if provider else [],
            'peak_cpu_active':peak_cpu,'peak_gpu_inflight':peak_gpu,'cpu_worker_pids':sorted(worker_pids),
            'cpu_worker_cores':sorted(worker_cores),'runtime_revision':runtime_revision,'host_partition':host_partition,
            'cache_initialization':provider.warmup if provider else None,
            'latest_gpu_sample':gpu_samples[-1] if gpu_samples else None,
            'engine_batch_stats':getattr(provider,'engine_stats',{}) if provider else {},
            'cache_admission':provider.admission.snapshot() if provider and hasattr(provider,'admission') else {}})
    def execute(item,meta):
        def materialize(entry,dest):return buffer.publish(meta,dest,entry)
        timing=meta['timing'] if meta and meta['boot_id']==boot else None
        try:
            result=session.run(item,materialize,score_context,validate_request,prepared_timing=timing)
            if meta and meta['boot_id']!=boot and result.get('status')!='paused':
                result['continuous_cold_seconds']=None;result['cold_timing_unavailable']='prepared_before_reboot'
                result['compile_seconds']=meta['timing']['compile_seconds'];result['runtime_revision']=runtime_revision
                save(session.root/'completed'/(item['key']+'.json'),result)
            return result
        except BaseException as exc:
            # Do not fail other requests that are still draining successfully.
            with session.calls.connect() as db:
                pending=db.execute("SELECT id FROM calls WHERE call_key=? AND state='started'",('rq43/'+item['key'],)).fetchall()
            for (attempt,) in pending:session.calls.finish(attempt,{'error':repr(exc)},'infrastructure_failure')
            raise
    try:
        if smoke and read(RQ/'configs/execution_v9.json').get('accelerator_enabled'):
            save(root/'fast_kernel_probe.json',gpu_fast_kernel_probe())
        if smoke and read(RQ/'configs/execution_v9.json').get('compiled_norms'):
            save(root/'normalizer_probe.json',gpu_norm_probe())
        for sig in (signal.SIGINT,signal.SIGTERM):handlers[sig]=signal.signal(sig,pause)
        save(root/'recovery'/str(time.time_ns()),session.recover())
        for item in items:
            done=session.completed(item['key'])
            if done:
                if done['request_hash']!=item['identity']:raise ValueError('Committed identity mismatch')
                completed.add(item['key'])
        if (session.root/'PAUSE').exists():progress('paused');return
        buffer=RamPreparationBuffer(root/('ram_v9_'+str(time.time_ns())))
        states=session.calls.latest_states()
        pending=[i for i in items if i['key'] not in completed and not i.get('reference') and
                 i['key'] not in prepared and states.get(i['key'])!='complete']
        ctx=mp.get_context('spawn');coreq=ctx.Queue();cores=host_partition['preparation_cores']
        if len(cores)!=8:raise RuntimeError('Eight distinct physical CPU cores required')
        for core in cores:coreq.put(core)
        cpu_pool=ProcessPoolExecutor(max_workers=8,mp_context=ctx,initializer=prepare_initializer,initargs=(coreq,))
        gpu_pool=ThreadPoolExecutor(max_workers=8,thread_name_prefix='rq43-gpu')
        attention_cases={r['id'] for r in mechanism_rows()}
        admitted=read(RQ/'results/gpu_smoke_v7/report.json').get('attention_enabled',False)
        while pending or preparing or running or cursor<len(items) or audit_pending or auditing:
            if deadline is not None and time.monotonic()>=deadline and not errors:
                errors.append({'stage':'deadline','error':'shared 600-second smoke budget exhausted'})
                save(session.root/'PAUSE',{'reason':'smoke_deadline'})
            paused=(session.root/'PAUSE').exists()
            # Refill CPU immediately, regardless of the number of ready images.
            prepare_slots=4 if audit_pending and len(metadata)>=16 else 8
            while pending and len(preparing)<prepare_slots and len(preparing)+len(auditing)<8 and not paused and buffer.can_prepare(len(preparing)):
                occupied={sources[x['id']].get('source',sources[x['id']].get('cloudbed',x['id'])) for x in preparing.values()}
                index=next((j for j,x in enumerate(pending[:32]) if sources[x['id']].get('source',sources[x['id']].get('cloudbed',x['id'])) not in occupied),0)
                item=pending.pop(index);dest=buffer.root/('v9_'+str(time.time_ns()))
                attention=item.get('attention',False) if smoke else admitted and item['id'] in attention_cases and item['arm'] in {'U','P_LOCAL_BI','C_GLOBAL_BI'}
                preparing[cpu_pool.submit(prepare_formal,item,str(dest),attention)]=item
                peak_cpu=max(peak_cpu,len(preparing)+len(auditing))
            while audit_pending and len(auditing)<4 and len(preparing)+len(auditing)<8 and not paused and (len(metadata)>=16 or not pending):
                row=audit_pending.pop(0);auditing[cpu_pool.submit(prepare_restoration,row,str(audit_folder))]=row
                peak_cpu=max(peak_cpu,len(preparing)+len(auditing))
            for future in [f for f in auditing if f.done()]:
                row=auditing.pop(future);out=future.result();restoration_summary(audit_folder)
                print('CPU_RESTORATION',row['id'],out['status'],flush=True)
            for future in [f for f in preparing if f.done()]:
                item=preparing.pop(future)
                try:
                    meta=future.result();metadata[item['key']]=meta;buffer.add(meta);prepared.add(item['key'])
                    worker_pids.add(meta['timing']['pid']);worker_cores.add(meta['timing']['core'])
                except BaseException as exc:
                    errors.append({'stage':'CPU','key':item['key'],'error':repr(exc),'traceback':traceback.format_exc()})
                    save(session.root/'PAUSE',{'reason':'CPU failure'});paused=True
            for future in [f for f in running if f.done()]:
                item=running.pop(future)
                try:
                    result=future.result()
                    if result.get('status')!='paused':
                        completed.add(item['key']);print('COMMITTED',item['key'],result['outcome']['status'],flush=True)
                except BaseException as exc:
                    errors.append({'stage':'GPU_or_commit','key':item['key'],'error':repr(exc),'traceback':traceback.format_exc()})
                    save(session.root/'PAUSE',{'reason':'GPU/commit failure'});paused=True
            # Submission order stays frozen; CPU completion order is immaterial.
            while cursor<len(items) and len(running)<8 and not paused:
                # Fail-fast qualification: one long-text call must commit before
                # any remaining smoke model calls. CPU preparation may run ahead.
                if smoke and queue.get('first_call_barrier') and cursor>0 and items[0]['key'] not in completed:break
                item=items[cursor];key=item['key']
                if key in completed:cursor+=1;continue
                if item.get('reference'):
                    if item['reference'] not in completed:break
                    session.run(item,None,score_context,validate_request);completed.add(key);cursor+=1;continue
                if states.get(key)=='complete':
                    session.run(item,None,score_context,validate_request);completed.add(key);cursor+=1;continue
                if key not in prepared:break
                if provider is None:
                    from .utils import execution_folder
                    engine_class=VLLMSolvers if execution_folder(scope).name in {'deployment_v13','deployment_v15','deployment_v16','deployment_v17'} else ConcurrentSolvers
                    progress('model_loading');provider=engine_class(scope,root/'attention'/str(time.time_ns()),deadline);session.provider=provider
                    save(root/'initialization'/str(time.time_ns()),provider.warmup)
                meta=metadata.pop(key);running[gpu_pool.submit(execute,item,meta)]=item
                launched.add(key);cursor+=1;peak_gpu=max(peak_gpu,len(running))
            if paused and not preparing and not running and not auditing:break
            if time.monotonic()-last_progress>2:
                progress('draining' if paused else 'running');last_progress=time.monotonic()
            if preparing or running or auditing:wait([*preparing,*running,*auditing],timeout=.1,return_when=FIRST_COMPLETED)
            elif cursor<len(items) and not pending and not paused:raise RuntimeError('Unresolved dependency without live owner')
            else:time.sleep(.1)
        progress('draining')
        cpu_pool.shutdown(wait=True,cancel_futures=True);cpu_pool=None;gpu_pool.shutdown(wait=True);gpu_pool=None
        if provider:provider.close();provider=None
        if errors:raise RuntimeError(repr(errors))
        if len(completed)<len(items):progress('paused');return
        phase={'status':'complete','positions':len(items),'queue_sha256':digest(path),'writers_drained':True,
            'calls':session.calls.summary(),'execution_fingerprint':execution_fingerprint(),
            'cpu_worker_pids':sorted(worker_pids),'cpu_worker_cores':sorted(worker_cores),
            'peak_cpu_active':peak_cpu,'peak_gpu_inflight':peak_gpu,'runtime_revision':runtime_revision,'host_partition':host_partition}
        phase['peak_RAM_buffer_bytes']=buffer.peak;phase['RAM_buffer_limit_bytes']=buffer.capacity
        if smoke:
            records=[session.completed(i['key']) for i in items]
            if peak_gpu!=8 or len(worker_pids)!=8 or len(worker_cores)!=8:raise RuntimeError('Eight-way runtime was not exercised')
            if any(r['usage'].get('attention_error') or r['usage'].get('attention_missed') for r in records):raise RuntimeError('Attention capture failed')
            on=next(r for i,r in zip(items,records) if i.get('attention'))
            off=next(r for i,r in zip(items,records) if not i.get('attention') and r['request_hash']==on['request_hash'])
            if off['response']!=on['response']:raise RuntimeError('Identical off/on request differs')
            def overlap(start):
                events=sorted((r['usage'][k],delta) for r in records for k,delta in [(start,1),('finished_monotonic',-1)])
                count=peak=0
                for _,delta in events:count+=delta;peak=max(peak,count)
                return peak
            active_peak=overlap('admitted_monotonic');decode_peak=overlap('prefill_done_monotonic')
            if active_peak!=8 or decode_peak<2:raise RuntimeError('Eight request slots or overlapping decode not observed')
            phase.update(status='passed',elapsed_seconds=time.time()-read(clock)['started_unix'],
                measured_request_overlap=active_peak,measured_decode_overlap=decode_peak,
                model_failures=sum(r['outcome']['status']=='model_failure' for r in records))
            if phase['elapsed_seconds']>600:raise TimeoutError('Smoke completion exceeded deadline')
            save(root/'report.json',phase)
        save(root/'phase_complete.json',phase);progress('complete');return phase
    except BaseException as exc:
        save(session.root/'PAUSE',{'reason':'concurrent runner failure'})
        # Drain live GPU work before recording the final failure, preserving answers.
        if gpu_pool:gpu_pool.shutdown(wait=True);gpu_pool=None
        for future,item in running.items():
            if future.done() and not future.exception() and session.completed(item['key']):completed.add(item['key'])
        record={'status':'failed','error':repr(exc),'details':errors,'traceback':traceback.format_exc(),'time':time.time()}
        save(root/'BLOCKED.json',record)
        if smoke:save(root/'report.json',record)
        progress('blocked');raise
    finally:
        if cpu_pool:cpu_pool.shutdown(wait=True,cancel_futures=True)
        if gpu_pool:gpu_pool.shutdown(wait=True)
        try:
            if provider:provider.close()
        finally:
            save(root/'gpu_utilization.json',{'interval_seconds':2,'samples':gpu_samples})
            if gpu_samples:__import__('pynvml').nvmlShutdown()
            session.close();owner.close()
            if buffer:buffer.close()
            for sig,old in handlers.items():signal.signal(sig,old)


def gpu_norm_probe():
    """GPU compatibility of compiled and already-fused normalization paths."""
    import torch,time
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5RMSNorm,Qwen3_5RMSNormGated
    from .utils import compiled_normalizers
    torch.manual_seed(431006);torch.cuda.set_per_process_memory_fraction(.75);torch.set_num_threads(1)
    plain,gated=compiled_normalizers();records=[];began=time.monotonic()
    with torch.inference_mode():
        for length in (1,129):
            for width in (128,256,5120):
                x=torch.randn(1,length,width,device='cuda',dtype=torch.bfloat16)
                for cls,fn in ((Qwen3_5RMSNorm,plain),(Qwen3_5RMSNormGated,gated)):
                    m=cls(width).to(device='cuda',dtype=torch.bfloat16);m.weight.copy_(torch.randn_like(m.weight)*.1)
                    if cls is Qwen3_5RMSNorm:
                        expected=m(x);actual=fn(x.reshape(-1,width),m.weight,m.eps).reshape_as(x)
                    else:
                        gate=torch.randn_like(x);expected=m(x,gate)
                        actual=fn(x.reshape(-1,width),m.weight,m.variance_epsilon,gate.reshape(-1,width)).reshape_as(x)
                    passed=bool(torch.allclose(actual.float(),expected.float(),atol=.005,rtol=.03))
                    records.append({'shape':list(x.shape),'kind':cls.__name__,'passed':passed,
                        'max_abs_error':float((actual.float()-expected.float()).abs().max()),'equal_fraction':float((actual==expected).float().mean())})
                    if not passed:raise ValueError('Compiled normalization mismatch: '+repr(records[-1]))
        from .utils import accelerator_identity
        if accelerator_identity():
            from fla.modules import FusedRMSNormGated
            for length in (1,129):
                x=torch.randn(length,128,device='cuda',dtype=torch.bfloat16);gate=torch.randn_like(x)
                native=Qwen3_5RMSNormGated(128,eps=1e-6).to(device='cuda',dtype=torch.bfloat16)
                fused=FusedRMSNormGated(128,eps=1e-6,activation='silu').to(device='cuda',dtype=torch.bfloat16)
                native.weight.copy_(torch.randn_like(native.weight)*.1);fused.weight.copy_(native.weight)
                expected=native(x,gate);actual=fused(x,gate)
                passed=bool(torch.allclose(actual.float(),expected.float(),atol=.005,rtol=.03))
                records.append({'shape':list(x.shape),'kind':'FusedRMSNormGated','passed':passed,
                    'max_abs_error':float((actual.float()-expected.float()).abs().max()),'equal_fraction':float((actual==expected).float().mean())})
                if not passed:raise ValueError('FLA normalization mismatch: '+repr(records[-1]))
    torch.cuda.synchronize();torch.cuda.empty_cache()
    return {'status':'passed','records':records,'seconds':time.monotonic()-began,
        'precision_casts':'compiled norms preserve BF16 intermediate rounding; FLA norm uses its native fused accumulation',
        'atol':.005,'rtol':.03}


def gpu_fast_kernel_probe():
    """Small independent GPU comparisons within the same smoke clock, no LLM calls."""
    import torch,time
    import torch.nn.functional as F
    from transformers.models.qwen3_5 import modeling_qwen3_5 as native
    from .utils import accelerator_identity
    identity=accelerator_identity(verify=True)
    if not native.is_fast_path_available:raise RuntimeError('Both FLA and causal-conv1d are required')
    torch.manual_seed(431005);torch.set_num_threads(1);torch.cuda.set_per_process_memory_fraction(.75)
    checks=[];began=time.monotonic()
    def compare(name,got,expected):
        error=float((got.float()-expected.float()).abs().max())
        passed=bool(torch.allclose(got.float(),expected.float(),atol=.005,rtol=.03))
        checks.append({'name':name,'max_abs_error':error,'passed':passed,'atol':.005,'rtol':.03})
        if not passed:raise ValueError('Fast kernel numerical mismatch: '+repr(checks[-1]))
    with torch.inference_mode():
        for length in (1,129,513):
            q,k,v=[torch.randn(1,length,2,128,device='cuda',dtype=torch.bfloat16) for _ in range(3)]
            g=-torch.rand(1,length,2,device='cuda');beta=torch.rand(1,length,2,device='cuda',dtype=torch.bfloat16)
            initial=torch.randn(1,2,128,128,device='cuda')*.01 if length==1 else None
            slow=native.torch_recurrent_gated_delta_rule if length==1 else native.torch_chunk_gated_delta_rule
            fast=native.fused_recurrent_gated_delta_rule if length==1 else native.chunk_gated_delta_rule
            args=dict(g=g,beta=beta,initial_state=initial,output_final_state=True,use_qk_l2norm_in_kernel=True)
            a=slow(q,k,v,**args);b=fast(q,k,v,**args)
            for i,name in enumerate(('output','state')):compare(f'GDN_{length}_{name}',b[i],a[i])
        x=torch.randn(1,64,129,device='cuda',dtype=torch.bfloat16)*.1
        weight=torch.randn(64,4,device='cuda',dtype=torch.bfloat16)*.1
        expected=F.silu(F.conv1d(x,weight[:,None,:],padding=3,groups=64)[:,:,:129])
        compare('conv_prefill',native.causal_conv1d_fn(x,weight,activation='silu'),expected)
        a=torch.randn(1,64,4,device='cuda',dtype=torch.bfloat16)*.1;b=a.clone()
        tick=x[:,:,-1:]
        expected=native.torch_causal_conv1d_update(tick,a,weight,None,'silu')
        compare('conv_decode',native.causal_conv1d_update(tick,b,weight,None,activation='silu'),expected)
        compare('conv_state',b,a)
    torch.cuda.synchronize();torch.cuda.empty_cache()
    return {'status':'passed','checks':checks,'accelerator':identity,'seconds':time.monotonic()-began,
        'claim':'BF16 numerical tolerance, not bitwise equivalence or unchanged RCA ranking'}


def gpu_operator_probe():
    """Non-generative BF16 operator check within the shared smoke clock."""
    import torch
    from .utils import RQ,save
    from .tests import recurrence_reference,PrefillIntegration
    torch.manual_seed(4303)
    q=torch.randn(1,65,3,8,dtype=torch.bfloat16,device='cuda')
    k=torch.randn_like(q);v=torch.randn_like(q)
    g=-torch.rand(1,65,3,dtype=torch.bfloat16,device='cuda');beta=torch.rand_like(g)
    groups=[list(range(1,25)),list(range(29,63))];actual=grouped_delta(q,k,v,g,beta,groups)
    expected=torch.zeros_like(v,dtype=torch.float32,device='cpu')
    for group in groups:
        for order in (group,list(reversed(group))):
            expected[:,order]+=recurrence_reference(*[x[:,order].float().cpu() for x in (q,k,v,g,beta)])/2
    error=float((actual.float().cpu()-expected).abs().max())
    torch.testing.assert_close(actual.float().cpu(),expected,atol=.025,rtol=.025)
    # λ=0 must leave actual BF16 native hidden states exactly unchanged.
    model=PrefillIntegration.tiny_model().to(device='cuda',dtype=torch.bfloat16);tokens=torch.arange(24,device='cuda')[None,:]
    with torch.inference_mode():baseline=model(tokens,use_cache=False).last_hidden_state
    adapter=VisualPrefillAdapter(model,[list(range(3,11)),list(range(11,19))],list(range(3,19)),mode='P_DUAL',weight=0)
    with torch.inference_mode(),adapter.prefill():replay=model(tokens,use_cache=False).last_hidden_state
    if not torch.equal(baseline,replay):raise ValueError('BF16 lambda-zero path changed')
    adapter.close();del model;torch.cuda.empty_cache();torch.set_num_threads(8)
    save(RQ/'results/gpu_smoke_v7/operator_probe.json',{'status':'passed','independent_BF16_max_abs_error':error,
        'atol':.025,'rtol':.025,'lambda_zero_bitwise':True,'model_calls':0})


def xs_probe(rows,folder):
    """v8: fixed S selection, new registered source components, real CPU render."""
    from .utils import save
    from .utils import RQ
    folder.mkdir(parents=True,exist_ok=True);prepared=[]
    for row in rows:
        d=folder/'inputs'/row['id'];d.mkdir(parents=True,exist_ok=True)
        original=ROOT/row['base'];s=RQ/'results/cpu_render_v6/population01/inputs'/row['id']/'S_JOINT'
        evidence=read(s/'evidence.json');design=read(s/'design.json')
        def visit(n):
            if n['type']=='panel':
                kind=next(c['kind'] for c in evidence['cards'] if c['id']==n['card'])
                if kind in {'metric','trace','log','inventory','comparison','graph'}:
                    n['component']=kind+'.source_compact';n.pop('node_layout',None);n.pop('dashed_width_scale',None)
            for child in n.get('children',[]):visit(child)
        visit(design['tree']);design.pop('presentation',None)
        save(d/'evidence.json',evidence);save(d/'design.json',design)
        save(d/'provenance.json',read(s/'provenance.json'))
        save(d/'processor_cpu.json',read(original/'processor_cpu.json'))
        geometry=read(original/'render/geometry.json');keep={c['id']:c for c in evidence['cards']}
        geometry['rectangles']=[r for r in geometry['rectangles'] if r['card'] in keep]
        for r in geometry['rectangles']:
            kind=keep[r['card']]['kind']
            if kind in {'metric','trace','log','inventory','comparison','graph'}:r['component']=kind+'.source_compact'
        save(d/'render/geometry.json',geometry)
        prepared.append(dict(row,base=str(d.relative_to(ROOT))))
    return reflow_probe(prepared,folder/'probe','source_scopes_pack_v4')


def source_label_aliases():
    import ast,re
    text=(ROOT/'src/renderer/web/components/SourceCompact.tsx').read_text()
    aliases=ast.literal_eval(re.search(r'sourceLabelAliases:Record<string,string>=(\{.*?\});',text,re.S)[1])
    if len(set(aliases.values()))!=len(aliases):raise ValueError('Ambiguous static field alias')
    return aliases


def xs_prompt(prompt):
    glossary='; '.join(f'{v} = {k}' for k,v in source_label_aliases().items())
    note='\nFixed field-label glossary (applies only to labels; values and units retain their displayed spelling): '+glossary+'.\n'
    boundary='<|im_end|>\n<|im_start|>assistant'
    if prompt.count(boundary)!=1:raise ValueError('Unknown prompt boundary')
    return prompt.replace(boundary,note+boundary)


def xs_caption_audit(evidence,render):
    """Independently invert the visible scope tree, not its hidden full-name attr."""
    inverse={v:k for k,v in source_label_aliases().items()}
    rows=read(render/'readability.json')['prefixes'];got={r['binding']:r for r in rows}
    expected={f"{c['id']}.detail.{i}":d for c in evidence['cards'] for i,d in enumerate(c['data'].get('details',[]))}
    if len(got)!=len(rows) or set(got)!=set(expected):raise ValueError('Caption occurrence lost or duplicated')
    for binding,d in expected.items():
        name=' · '.join(inverse.get(p,p) for p in got[binding]['name'].split(' · '))
        if name!=d['name'] or got[binding]['value']!=d['value']:raise ValueError('Non-reversible visible caption '+binding)
    return {'status':'passed','occurrences':len(expected),'value_strings_exact':True,'visible_label_roundtrip':True}


def xs_case(row,dest,processor,existing=None,prepared_render=None):
    """Qualify X_SRP against its actual selected input; never relax original N/K."""
    from .utils import RQ,HISTORY,save,digest
    from RQs.RQ4_1.src.utils import foreground_support
    from RQs.RQ4_1.src.exps import ledger
    if existing is None:
        if prepared_render is not None:
            import shutil
            base_render=dest/'layout/probe'/row['id']/'render'
            shutil.copytree(prepared_render,base_render,dirs_exist_ok=True)
            summary={'render_status':read(base_render/'manifest.json')['status']}
        else:
            summary=xs_probe([row],dest/'layout')[0];base_render=dest/'layout/probe'/row['id']/'render'
        if summary.get('status')=='no_capacity_layout_in_registered_finite_set':
            req=registered_request(row,'X_SP');save(dest/'request.json',req)
            return {'id':row['id'],'dataset':row['dataset'],'status':'completed','qualified':False,'reason':'no_layout_within_original_N','fallback':'X_SP','new_model_calls':0}
        if summary.get('render_status')!='passed':raise ValueError('Unresolved rendering bug: '+repr(summary))
        packed=pack_probe(row,base_render,dest/'packed');render=ROOT/packed.get('final_render',str((dest/'packed/render').relative_to(ROOT)))
    else:
        base_render=existing/'render';packed=read(existing/'packed12/result.json');render=ROOT/packed['final_render']
    if packed['render_status']!='passed' or not packed['prediction_exact']:raise ValueError('Packing/render mismatch '+repr(packed))
    evidence=read(render/'evidence.json');s=RQ/'results/cpu_render_v6/population01/inputs'/row['id']/'S_JOINT'
    if evidence!=read(s/'evidence.json'):raise ValueError('Selected public fields changed')
    caption=xs_caption_audit(evidence,render)
    reduction=1-packed['actual_anchors']/packed['before_anchors']
    original=ROOT/row['base'];old=read(HISTORY/f"formal_v28/completed/{row['id']}__development__A_UNIFORM_E50__BASE.json")
    maximum=len(old['actual_retention']['indices']);request=registered_request(row,'X_SP')
    result={'id':row['id'],'dataset':row['dataset'],'status':'completed','qualified':False,'anchors':packed['actual_anchors'],
        'K':maximum,'before_anchors':packed['before_anchors'],'anchor_reduction':reduction,'caption_audit':caption,'new_model_calls':0}
    if not packed['anchor_cap_pass'] or reduction<.10:
        save(dest/'request.json',request);result.update(reason='R_budget_or_intervention_inapplicable',fallback='X_SP');return result
    manifest=read(render/'manifest.json');prompt=xs_prompt(request['prompt']);processed=[manifest['width'],manifest['height']]
    support=foreground_support(render,processed,policy='shared_v2')
    if support['definite_empty_unanchored_roles'] or support['uncertain_empty_unanchored_roles']:
        raise ValueError('Unresolved actual source glyphs '+repr(support['definite_empty_unanchored_roles']+support['uncertain_empty_unanchored_roles']))
    # Spend released anchor slots on actual observation support, up to original K.
    retained=uniform_support_indices(support,limit=maximum)
    actual=processor_audit(processor,render/'dashboard.png',prompt,read(original/'processor_cpu.json')['image_tokens'],retained['indices'])
    if actual['processed_pixels']!=processed:raise ValueError('Unregistered resize in compact grid')
    save(dest/'evidence.json',evidence);save(dest/'design.json',read(render/'design.json'))
    save(dest/'token_support.json',support);save(dest/'retention.json',retained)
    save(dest/'provenance.json',read(s/'provenance.json'));save(dest/'processor.json',actual)
    public=read(ROOT/f"RQs/RQ3_21/preparation/compact_entity_v1/public/{row['id']}.json")
    groups=source_token_groups(dict(row,base=str(dest.relative_to(ROOT))),ledger(public),read(original/'mapping.json'),evidence,manifest['rectangles'],actual,retained['indices'])
    save(dest/'groups.json',groups)
    request.update(prompt=prompt,image=str((render/'dashboard.png').relative_to(ROOT)),manifest=str((render/'manifest.json').relative_to(ROOT)),
        retained=retained['indices'],groups=groups,processor=actual,operation='P_LOCAL_BI' if groups['qualified'] else 'U')
    save(dest/'request.json',request)
    result.update(qualified=True,P_qualified=groups['qualified'],P_coverage=groups['coverage'],processor=actual,
        retained=len(retained['indices']),png_sha256=digest(render/'dashboard.png'),image=request['image'],request=str((dest/'request.json').relative_to(ROOT)))
    return result


def predict_anchor_offsets(alpha,dom,offsets):
    import numpy as np
    alpha=np.asarray(alpha)>0;h,w=alpha.shape;owner=np.zeros((h,w),np.uint16);bounds=[]
    for b in dom['blocks']:
        x,y,bw,bh=b['box'];bb=(max(0,math.floor(x)-1),max(0,math.floor(y)-1),min(w,math.ceil(x+bw)+1),min(h,math.ceil(y+bh)+1))
        bounds.append(bb);x0,y0,x1,y1=bb;owner[y0:y1,x0:x1]+=1
    shifts={m['id']:(m['dx'],m['dy']) for m in offsets};yy,xx=np.nonzero(alpha&(owner!=1));tokens=set((yy//32*(w//32)+xx//32).tolist())
    for b,(x0,y0,x1,y1) in zip(dom['blocks'],bounds,strict=True):
        yy,xx=np.nonzero(alpha[y0:y1,x0:x1]&(owner[y0:y1,x0:x1]==1));dx,dy=shifts.get(b['id'],(0,0))
        tokens.update(((yy+y0+dy)//32*(w//32)+(xx+x0+dx)//32).tolist())
    return sorted(tokens)


def extend_xs_queue():
    """Append prospective X_SRP positions; keep the original queue byte-for-byte."""
    from .utils import RQ,roster,save,digest,generation_identity
    old=read(RQ/'results/deployment_v7/queue.json');folder=RQ/'results/deployment_v8'
    report=read(RQ/'results/xsrp_v8/population02/report.json')
    if report['status']!='passed' or report['completed']!=220 or report['errors']:raise RuntimeError('X_SRP population not qualified')
    items=list(old['items']);owners={}
    for item in items:
        if item['variant']!='REPEAT':owners.setdefault(item['identity'],item['key'])
    for row in sorted(roster(),key=lambda r:stable(['rq43-xs-append-v8',r['id']])):
        req=registered_request(row,'X_SRP');identity=generation_identity(req,old['model_fingerprint']);req['identity']=identity
        key=row['id']+'__X_SRP__BASE';path=folder/'requests'/(key+'.json');save(path,req)
        items.append({'key':key,'id':row['id'],'dataset':row['dataset'],'event_group':row['event_group'],
            'arm':'X_SRP','variant':'BASE','task':'RCA','identity':identity,'request':str(path.relative_to(ROOT)),
            'request_sha256':digest(path),'reference':owners.get(identity)})
        owners.setdefault(identity,key)
    if len(items)!=2632 or items[:2412]!=old['items']:raise ValueError('Append changed original queue')
    result={**old,'schema':'RQ43FrozenQueueV8','items':items,'positions':2632,
        'unique_calls':sum(not i['reference'] for i in items),'preselected_status':'X_SRP_restored_CPU_user_GPU_waiver',
        'cancelled':{k:v for k,v in old['cancelled'].items() if k!='X_SRP'},
        'original_queue_sha256':digest(RQ/'results/deployment_v7/queue.json'),'append_block_order_disclosed':True}
    save(folder/'queue.json',result);return result


RESTORED_ARMS=('R_PATCH_PACK','R_HORIZON','R_PACK_HORIZON','C_PACK_OFFSET',
               'C_READ_GUIDE','C_PACK_BG_FILL','X_SR','X_RP')


def r14_aliases():
    import re,json
    text=(ROOT/'src/renderer/web/components/PackedSource.tsx').read_text()
    aliases=json.loads(re.search(r'packedLabelAliases:Record<string,string>=(\{.*?\});',text,re.S)[1])
    if len(set(aliases.values()))!=len(aliases):raise ValueError('Ambiguous fixed field grammar')
    return aliases


def r14_prompt(prompt):
    names={}
    for aliases in (source_label_aliases(),r14_aliases()):
        for key,value in aliases.items():
            if value in names and names[value]!=key:raise ValueError('Conflicting shared reading convention')
            names[value]=key
    glossary='; '.join(f'{v} = {k}' for v,k in names.items())
    note='\nFixed drawing conventions, when present: field labels use this glossary: '+glossary+'. '
    note+='Entity IDs retain all digits: 3 digits encode service, 4 node, 5 pod and 6 external. Numeric-only labels use exactly this fixed type grammar. '
    note+='In compact source scopes, cur/ref may appear after the measure and unit; μ means mean, σ means standard deviation. Bold scope headings apply to their enclosed fields. '
    note+='Only field names are shortened; values and units keep their displayed spelling. '
    note+='Horizon charts use two folded magnitude bands about zero: positive blue, negative orange; darker means the second band. '
    note+='The chart labels show 0, band width b and 2b in the original unit; color denotes sign and band, not reference/current. '
    note+='Retain the displayed entity, source and phase bindings when reading the chart.\n'
    boundary='<|im_end|>\n<|im_start|>assistant'
    if prompt.count(boundary)!=1:raise ValueError('Unknown task boundary')
    return prompt.replace(boundary,note+boundary)


def r14_caption_name(name):
    aliases=r14_aliases();parts=[aliases.get(x,x) for x in name.split(' · ')];phase=None;out=[]
    known={'μ':'mean','σ':'std_dev','median':'median','MAD':'mad','samples':'samples','interval s':'interval_s',
           'spans':'span count','excl95':'exclusive p95','incl95':'inclusive p95'}
    for part in parts:
        if part in ('cur','ref'):phase=part
        elif len(part)>2 and part[:2] in ('C ','R ') and part[2:] in known:
            phase='cur' if part[0]=='C' else 'ref';out.append({'excl95':'exclusive p95','incl95':'inclusive p95'}.get(part[2:],part[2:]))
        else:out.append(part)
    if phase:out.append(phase)
    return ' · '.join(out)


def r14_caption_audit(evidence,render):
    rows=read(render/'readability.json')['prefixes'];got={r['binding']:r for r in rows}
    expected={f"{c['id']}.detail.{i}":d for c in evidence['cards'] for i,d in enumerate(c['data'].get('details',[]))}
    if len(got)!=len(rows) or set(got)!=set(expected):raise ValueError('Lost/duplicated detail occurrence')
    for binding,d in expected.items():
        name=r14_caption_name(d['name'])
        if got[binding]['name']!=name or got[binding]['value']!=d['value']:raise ValueError('Visible caption roundtrip failed '+binding)
    return {'status':'passed','occurrences':len(expected),'values_exact':True,'visible_names_reversible':True}


def r14_layouts(evidence,original,measurement,maximum):
    """Whole-card columns with a real 32px outer gutter for a 16px control.

    Uses existing row/column/spacer layouts. No off-grid region override, crop,
    processor change, or evidence reduction. All sizes come from the real DOM.
    """
    from copy import deepcopy
    nodes={}
    def visit(n):
        if n['type']=='panel':nodes[n['card']]=deepcopy(n)
        for child in n.get('children',[]):visit(child)
    visit(original['tree']);order=[c['id'] for c in evidence['cards']];out=[]
    for m in measurement['measurements']:
        w=m['region_width'];sizes={r['card']:r for r in m['cards']}
        if set(sizes)!=set(order):raise ValueError('Card measurement mismatch')
        bad=[r['card'] for r in m['cards'] if r['overflow'] or r['min_font']<17.999]
        for count in range(2,(8192-32)//w+1):
            columns=[[] for _ in range(count)];heights=[0]*count
            for cid in sorted(order,key=lambda cid:(-sizes[cid]['height'],order.index(cid))):
                i=min(range(count),key=lambda j:(heights[j],j));h=sizes[cid]['height']
                columns[i].append((cid,h));heights[i]+=h
            height=math.ceil((max(heights)+96)/32)*32;width=count*w+32
            design=deepcopy(original);design.pop('evidence_regions',None);design.pop('provenance',None)
            design.update(viewport={'width':width,'height':height},canvas_extent='wide_8192_v1',gap=0,padding=0,
                font_size=18,readable_cards='source_scopes_pack_v4',readability_audit='VisibleSourceV1')
            cols=[]
            for i,col in enumerate(columns):
                children=[{'id':f'top{i}','type':'spacer'}]+[nodes[cid] for cid,h in col];weights=[10]+[h for cid,h in col]
                spare=height-86-sum(weights)
                if spare:children.append({'id':f'bottom{i}','type':'spacer'});weights.append(spare)
                cols.append({'id':f'column{i}','type':'column','children':children,'weights':weights})
            content={'id':'content','type':'row','children':cols,'weights':[w]*count}
            design['tree']={'id':'gutter','type':'row','children':[content,{'id':'right','type':'spacer'}],'weights':[count*w,32]}
            out.append({'width':width,'height':height,'area':width*height,'image_tokens':width*height//1024,
                'pass':not bad and height<=8192 and width*height//1024<=maximum,'bad_cards':bad,'design':design})
    out.extend(r14_graph_band(evidence,original,measurement,maximum,nodes))
    return sorted(out,key=lambda x:(1 if x.get('layout')=='wide_graph_band' else 0,x['area'],x['height'],x['width']))


def r14_graph_band(evidence,original,measurement,maximum,nodes):
    """Give existing node-link components width, without widening every chart.

    The old uniform-width compiler wasted area by enlarging all SVG plots when
    it widened a dense graph. Existing row/column/spacer operations suffice.
    """
    from copy import deepcopy
    ms={m['region_width']:{r['card']:r for r in m['cards']} for m in measurement['measurements']}
    if 512 not in ms or 1024 not in ms:return []
    graphs=[c['id'] for c in evidence['cards'] if c['kind']=='graph']
    ordinary=[c['id'] for c in evidence['cards'] if c['kind']!='graph']
    if not graphs or not ordinary:return []
    bad=[cid for cid in graphs+ordinary if ms[1024 if cid in graphs else 512][cid]['overflow'] or ms[1024 if cid in graphs else 512][cid]['min_font']<17.999]
    out=[]
    for count in range(4,16,2):
        bands=[];band_heights=[]
        for j in range(0,len(graphs),count//2):
            group=graphs[j:j+count//2];height=max(ms[1024][cid]['height'] for cid in group);children=[]
            for cid in group:
                h=ms[1024][cid]['height'];parts=[deepcopy(nodes[cid])];weights=[h]
                if height>h:parts.append({'id':cid+'pad','type':'spacer'});weights.append(height-h)
                children.append({'id':cid+'column','type':'column','children':parts,'weights':weights})
            while len(children)<count//2:children.append({'id':f'bandgap{j}_{len(children)}','type':'spacer'})
            bands.append({'id':f'graphband{j}','type':'row','children':children,'weights':[1024]*len(children)})
            band_heights.append(height)
        columns=[[] for _ in range(count)];heights=[0]*count
        for cid in sorted(ordinary,key=lambda c:(-ms[512][c]['height'],ordinary.index(c))):
            i=min(range(count),key=lambda j:(heights[j],j));h=ms[512][cid]['height'];columns[i].append((cid,h));heights[i]+=h
        body_height=max(heights);height=96+sum(band_heights)+body_height;width=count*512+32
        cols=[]
        for i,col in enumerate(columns):
            parts=[deepcopy(nodes[cid]) for cid,h in col];weights=[h for cid,h in col]
            if body_height>heights[i]:parts.append({'id':f'bodygap{i}','type':'spacer'});weights.append(body_height-heights[i])
            cols.append({'id':f'bodycol{i}','type':'column','children':parts,'weights':weights})
        body={'id':'bodyrow','type':'row','children':cols,'weights':[512]*count}
        content={'id':'content','type':'column','children':[{'id':'top','type':'spacer'}]+bands+[body],
            'weights':[10]+band_heights+[body_height]}
        design=deepcopy(original);design.pop('evidence_regions',None);design.pop('provenance',None)
        design.update(viewport={'width':width,'height':height},canvas_extent='wide_8192_v1',gap=0,padding=0,
            font_size=18,readable_cards='source_scopes_pack_v4',readability_audit='VisibleSourceV1')
        design['tree']={'id':'gutter','type':'row','children':[content,{'id':'right','type':'spacer'}],'weights':[count*512,32]}
        out.append({'width':width,'height':height,'area':width*height,'image_tokens':width*height//1024,
            'pass':not bad and height<=8192 and width*height//1024<=maximum,'bad_cards':bad,'design':design,'layout':'wide_graph_band'})
    return out



def r14_layout(row,dest,horizon=False):
    from renderer.measure import measure_jobs
    from renderer.main import render
    from .utils import save
    from copy import deepcopy
    base=ROOT/row['base'];evidence=read(base/'evidence.json');design=read(base/'design.json')
    def visit(n):
        if n['type']=='panel':
            kind=next(c['kind'] for c in evidence['cards'] if c['id']==n['card'])
            if kind in {'metric','trace','log','inventory','comparison','graph'}:
                n['component']='graph.numeric_source' if kind=='graph' else 'metric_horizon.source_compact' if kind=='metric' and horizon else kind+'_packed.source_compact'
                n.pop('node_layout',None);n.pop('dashed_width_scale',None)
        for child in n.get('children',[]):visit(child)
    visit(design['tree']);design.pop('presentation',None)
    save(dest/'evidence.json',evidence);save(dest/'design.json',design)
    geometry=read(base/'render/geometry.json');bykind={c['id']:c['kind'] for c in evidence['cards']}
    for r in geometry['rectangles']:
        kind=bykind[r['card']]
        if kind in {'metric','trace','log','inventory','comparison','graph'}:
            r['component']='graph.numeric_source' if kind=='graph' else 'metric_horizon.source_compact' if kind=='metric' and horizon else kind+'_packed.source_compact'
    save(dest/'render/geometry.json',geometry)
    job=reflow_job(dict(row,base=str(dest.relative_to(ROOT))),dest,'source_scopes_pack_v4')
    save(dest/'jobs.json',[job]);measure_jobs(dest/'jobs.json',dest/'measure.log')
    layouts=r14_layouts(evidence,design,read(dest/'dom.json'),read(base/'processor_cpu.json')['image_tokens'])
    save(dest/'layouts.json',layouts);good=[x for x in layouts if x['pass']]
    if not good:return {'status':'inapplicable','reason':'no_complete_readable_layout_within_N'}
    design=good[0]['design'];design['provenance']={'schema':'CanonicalForegroundV3','roles':[
        {k:r[k] for k in ('id','targets')} for r in read(base/'provenance.json')['roles']]}
    save(dest/'chosen_design.json',design);manifest=render(dest/'evidence.json',dest/'chosen_design.json',dest/'unpacked')
    if manifest['status']!='passed':raise ValueError('Renderer audit failed')
    caption=r14_caption_audit(evidence,dest/'unpacked')
    return {'status':'passed','render':str((dest/'unpacked').relative_to(ROOT)),'captions':caption,'N':good[0]['image_tokens']}


def r14_background_control(support,retention,original_optional,case_id):
    """Independent exact D accounting; real background only, no fake vectors."""
    anchors=set(support['anchors']);order=retention['optional_order'];k=len(retention['indices'])
    q=min(original_optional,k-len(anchors));delta=len(order)-q
    occupied=set(anchors)
    for role in support['roles'].values():occupied.update(role['foreground_possible_tokens'])
    occupied.update(support.get('all_visible_ink_tokens',[]))
    background=sorted(set(range(support['image_tokens']))-occupied-set(retention['indices']),key=lambda t:(stable(['rq43-bg-v1',case_id,t]),t))
    extra=set(order[q:]);observed=extra&occupied
    if delta<=0 or not observed or len(background)<delta:
        return {'qualified':False,'D':delta,'reason':'no_observed_extra_slots_or_insufficient_real_background','indices':retention['indices']}
    indices=sorted(anchors|set(order[:q])|set(background[:delta]))
    if len(indices)!=k or not anchors<=set(indices):raise ValueError('Background control changed K or anchors')
    return {'qualified':True,'indices':indices,'D':delta,'base_optional':q,'replaced':order[q:],
        'background':background[:delta],'observation_extra':len(observed),'observed_extra_fraction':len(observed)/delta}


def r14_all_ink_tokens(render):
    """Conservative real-PNG background audit, including unbound curve segments.

    Only exact flat body/card colors are removable background. Borders, axes,
    header and antialias pixels stay occupied; this can reject extra background,
    never silently call a plotted line or horizon area blank.
    """
    import numpy as np
    from PIL import Image
    design=read(render/'design.json');theme=design['theme']
    colors={'dark':((16,24,33),(24,36,47)),'light':((237,242,245),(255,255,255))}
    if theme not in colors:raise ValueError('Unregistered flat-background palette')
    with Image.open(render/'dashboard.png') as image:rgb=np.asarray(image.convert('RGB'))
    h,w=rgb.shape[:2]
    if h%32 or w%32:raise ValueError('Background grid is not exact processor grid')
    blank=np.zeros((h,w),bool)
    for color in colors[theme]:blank|=(rgb==color).all(axis=-1)
    ink=(~blank).reshape(h//32,32,w//32,32).any(axis=(1,3))
    return np.flatnonzero(ink).tolist()


def r14_render_request(row,render,dest,processor,prompt,operation='U',retention=None):
    from .utils import save,HISTORY,digest,RQ
    from RQs.RQ4_1.src.utils import foreground_support
    from RQs.RQ4_1.src.exps import ledger
    import shutil
    base=ROOT/row['base'];manifest=read(render/'manifest.json')
    if manifest['status']!='passed':raise ValueError('Unqualified renderer output')
    size=[manifest['width'],manifest['height']]
    support=foreground_support(render,size,policy='shared_v2')
    if support['definite_empty_unanchored_roles'] or support['uncertain_empty_unanchored_roles']:
        raise ValueError('Lost/ambiguous source operands in actual raster')
    original=read(HISTORY/f"formal_v28/completed/{row['id']}__development__A_UNIFORM_E50__BASE.json")
    cap=len(original['actual_retention']['indices'])
    if len(support['anchors'])>cap:
        return {'qualified':False,'reason':'mandatory_anchors_exceed_K','anchors':len(support['anchors']),'K':cap},None,support,None
    retained=uniform_support_indices(support,cap) if retention is None else retention
    if not set(support['anchors'])<=set(retained['indices']) or len(retained['indices'])>cap:raise ValueError('Retention violates mandatory anchors/budget')
    proc=processor_audit(processor,render/'dashboard.png',prompt,read(base/'processor_cpu.json')['image_tokens'],retained['indices'])
    if proc['processed_pixels']!=size:raise ValueError('Unexpected processor resize')
    evidence=read(render/'evidence.json');prov=read(base/'provenance.json')
    keep={c['id'] for c in evidence['cards']}
    selected=keep!={c['id'] for c in read(base/'evidence.json')['cards']}
    if selected:prov=read(RQ/'results/cpu_render_v6/population01/inputs'/row['id']/'S_JOINT/provenance.json')
    save(dest/'evidence.json',evidence);save(dest/'provenance.json',prov);save(dest/'token_support.json',support)
    save(dest/'retention.json',retained);save(dest/'processor.json',proc)
    public=read(ROOT/f"RQs/RQ3_21/preparation/compact_entity_v1/public/{row['id']}.json")
    groups=source_token_groups(dict(row,base=str(dest.relative_to(ROOT))),ledger(public),read(base/'mapping.json'),evidence,manifest['rectangles'],proc,retained['indices'])
    save(dest/'groups.json',groups)
    req=registered_request(row,'U');req.update(prompt=prompt,image=str((render/'dashboard.png').relative_to(ROOT)),
        manifest=str((render/'manifest.json').relative_to(ROOT)),retained=retained['indices'],groups=groups,processor=proc,
        operation=operation if operation=='U' or groups['qualified'] else 'U')
    save(dest/'request.json',req)
    return {'qualified':True,'N':proc['image_tokens'],'K':len(retained['indices']),'anchors':len(support['anchors']),
        'P_qualified':groups['qualified'],'P_coverage':groups['coverage'],'image':req['image'],
        'png_sha256':digest(render/'dashboard.png'),'processor':proc,'request':str((dest/'request.json').relative_to(ROOT))},req,support,retained


def r14_offset_design(design):
    from copy import deepcopy
    new=deepcopy(design);root=new['tree']
    if root['id']!='gutter' or root['weights'][-1]!=32:raise ValueError('No registered real control gutter')
    from renderer.operations.raster_translation import apply
    apply(new,16)
    return new


def r14_offset_audit(before,after):
    import numpy as np
    from PIL import Image
    a=read(before/'manifest.json');b=read(after/'manifest.json')
    if (a['width'],a['height'])!=(b['width'],b['height']):raise ValueError('Offset changed canvas')
    aa={r['key']:r for r in a['audit']['bindings']};bb={r['key']:r for r in b['audit']['bindings']}
    if aa.keys()!=bb.keys():raise ValueError('Offset lost binding')
    for k,x in aa.items():
        y=bb[k]
        if abs(y['x']-x['x']-16)>.02 or any(abs(y[f]-x[f])>.02 for f in ('y','width','height')):raise ValueError('Nonrigid bound-glyph displacement '+k)
    for name in ('anchor_foreground.png','role_foreground.png'):
        with Image.open(before/name) as x,Image.open(after/name) as y:
            x=np.asarray(x);y=np.asarray(y)
            if np.any(x[:,-16:,-1]) or np.any(y[:,:16,-1]) or not np.array_equal(x[:,:-16],y[:,16:]):
                raise ValueError('Offset raster is not an intact integer translation '+name)
    return {'status':'passed','processed_dx':16,'bindings':len(aa),'raster_exact':True}


def r14_case(row,dest,processor):
    from .utils import save,digest,HISTORY,RQ
    from renderer.main import render
    from copy import deepcopy
    base=ROOT/row['base'];ordinary=registered_request(row,'U');prompt=r14_prompt(ordinary['prompt'])
    guide=deepcopy(ordinary);guide['prompt']=prompt
    guide['processor']=processor_audit(processor,ROOT/guide['image'],prompt,read(base/'processor_cpu.json')['image_tokens'],guide['retained'])
    save(dest/'C_READ_GUIDE/request.json',guide)
    results={'C_READ_GUIDE':{'qualified':True,'request':str((dest/'C_READ_GUIDE/request.json').relative_to(ROOT))}}
    requests={'C_READ_GUIDE':guide};line_support=None;line_retention=None;line_render=None
    for horizon in (False,True):
        mode='horizon' if horizon else 'line';layout=r14_layout(row,dest/mode,horizon)
        save(dest/mode/'layout_result.json',layout)
        if layout['status']=='inapplicable':
            for arm in (('R_HORIZON','R_PACK_HORIZON') if horizon else ('R_PATCH_PACK',)):
                results[arm]={'qualified':False,'reason':layout['reason'],'fallback':'C_READ_GUIDE'};requests[arm]=guide
            continue
        unpacked=ROOT/layout['render']
        if read(unpacked/'evidence.json')!=read(base/'evidence.json'):raise ValueError('Full source facts changed')
        if horizon:
            info,req,_,_=r14_render_request(row,unpacked,dest/'R_HORIZON',processor,prompt)
            results['R_HORIZON']=info;requests['R_HORIZON']=req or guide
        packed=pack_probe(row,unpacked,dest/mode/'packed',accelerated=True)
        if packed.get('render_status')!='passed' or not packed.get('prediction_exact'):raise ValueError('Unresolved exact packing/render audit '+str(packed))
        reduction=1-packed['actual_anchors']/packed['before_anchors'];arm='R_PACK_HORIZON' if horizon else 'R_PATCH_PACK'
        if reduction<.10 or not packed['anchor_cap_pass']:
            results[arm]={'qualified':False,'reason':'R_intervention_or_K_gate','anchor_reduction':reduction,
                'anchors':packed['actual_anchors'],'K':packed['original_K'],'fallback':'C_READ_GUIDE'};requests[arm]=guide
        else:
            image=ROOT/packed['final_render'];r14_caption_audit(read(image/'evidence.json'),image)
            info,req,support,retained=r14_render_request(row,image,dest/arm,processor,prompt)
            info['anchor_reduction']=reduction;results[arm]=info;requests[arm]=req or guide
            if not horizon and info['qualified']:line_support=support;line_retention=retained;line_render=image
    if line_render is not None:
        rp=deepcopy(requests['R_PATCH_PACK']);rp['operation']='P_LOCAL_BI' if rp['groups']['qualified'] else 'U'
        results['X_RP']=dict(results['R_PATCH_PACK'],qualified=rp['groups']['qualified']);requests['X_RP']=rp
        old=read(HISTORY/f"formal_v28/completed/{row['id']}__development__A_UNIFORM_E50__BASE.json")
        oldsupport=read(base/'token_support.json');qu=len(set(old['actual_retention']['indices'])-set(oldsupport['anchors']))
        line_support['all_visible_ink_tokens']=r14_all_ink_tokens(line_render)
        bg=r14_background_control(line_support,line_retention,qu,row['id']);bgreq=deepcopy(requests['R_PATCH_PACK'])
        bgreq['retained']=bg['indices'];bgreq['groups']={}
        results['C_PACK_BG_FILL']=bg;requests['C_PACK_BG_FILL']=bgreq
        design=r14_offset_design(read(line_render/'design.json'));od=dest/'offset';save(od/'design.json',design)
        manifest=render(line_render/'evidence.json',od/'design.json',od/'render')
        if manifest['status']!='passed':raise ValueError('Offset renderer failed')
        offset_audit=r14_offset_audit(line_render,od/'render')
        info,req,_,_=r14_render_request(row,od/'render',dest/'C_PACK_OFFSET',processor,prompt)
        info['rigid_translation']=offset_audit;results['C_PACK_OFFSET']=info;requests['C_PACK_OFFSET']=req or requests['R_PATCH_PACK']
    else:
        for arm in ('X_RP','C_PACK_BG_FILL','C_PACK_OFFSET'):
            results[arm]={'qualified':False,'reason':'R_inapplicable','fallback':'C_READ_GUIDE'};requests[arm]=guide
        rp=deepcopy(registered_request(row,'P_LOCAL_BI'));rp['prompt']=prompt;rp['processor']=guide['processor']
        requests['X_RP']=rp;results['X_RP']['fallback']='P_LOCAL_BI_with_R_guide'
    # Keep the actual already-qualified selected S+R pixels and mask; no new
    # selection or unsafe reuse of a full-pool capacity failure for a subset.
    xs=RQ/'results/xsrp_v8/population02/completed'/(row['id']+'.json');prior=read(xs)
    sr=deepcopy(registered_request(row,'X_SRP'));sr['operation']='U';sr['prompt']=r14_prompt(registered_request(row,'S_JOINT')['prompt'])
    if not prior['qualified']:
        sr=deepcopy(registered_request(row,'S_JOINT'));sr.update(prompt=r14_prompt(sr['prompt']),operation='U')
    sr['processor']=processor_audit(processor,ROOT/sr['image'],sr['prompt'],read(base/'processor_cpu.json')['image_tokens'],sr['retained'])
    results['X_SR']={'qualified':bool(prior['qualified']),'reused_CPU_render':True,'source_revision':'X_SRP_v8',
        'anchor_reduction':prior.get('anchor_reduction'),'image':sr['image']};requests['X_SR']=sr
    for arm in RESTORED_ARMS:
        req=requests[arm]
        if req['processor']['retained_input_tokens']+8192>40960:raise ValueError('Context exceeded '+arm)
        save(dest/arm/'request.json',req);results[arm]['request']=str((dest/arm/'request.json').relative_to(ROOT))
        save(dest/arm/'qualification.json',results[arm])
    return {'id':row['id'],'dataset':row['dataset'],'status':'completed','arms':results,'new_model_calls':0}




def semantic_html_population(with_program=False):
    """One fully scoped user-authorized HTML comparator; never truncate facts."""
    from transformers import AutoTokenizer
    from renderer.semantic_html import export,decode,plot_program
    from .utils import save,HISTORY,RQ
    from collections import Counter
    tokenizer=AutoTokenizer.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    folder=RQ/('results/html_plot_code_v16' if with_program else 'results/html_semantic_v16');index=read(HISTORY/'deployment_v26/request_index.json')['requests'];rows=[]
    for row in __import__('RQs.RQ4_3.src.utils',fromlist=['roster']).roster():
        dest=folder/'inputs'/row['id'];evidence=read(ROOT/row['base']/'evidence.json')
        text=export(evidence,dest/'evidence.html')
        if with_program:
            text+=plot_program();(dest/'evidence.html').write_text(text)
        source=index[row['id']+'__VISUAL__BASE']['prompt']
        prompt=source.replace('<|vision_start|><|image_pad|><|vision_end|>','')
        prompt=prompt.replace('complete telemetry dashboard','complete semantic HTML evidence table').replace('in the image','in the HTML table').replace('image','HTML table')
        note='\nEvidence format: table headers name public card fields. Each cell uses JSON value syntax. Objects with columns and rows are lossless tables: each row follows those column names, including nested tables. Numeric values and strings retain their units and source scope. No rendered image is supplied.\n'
        boundary='<|im_end|>\n<|im_start|>assistant'
        if prompt.count(boundary)!=1:raise ValueError('Unknown task boundary')
        prompt=prompt.replace(boundary,note+text+boundary)
        n=len(tokenizer(prompt,add_special_tokens=False)['input_ids'])
        seed=read(HISTORY/f"formal_v28/completed/{row['id']}__development__A_UNIFORM_E50__BASE.json")['decoder_seed']
        req={'prompt':prompt,'image':None,'manifest':None,'retained':[],'groups':{},'operation':'TEXT','order':False,
            'seed':seed,'task':'RCA','attention':False,'processor':{'text_tokens':n,'image_tokens':0,'retained_input_tokens':n}}
        save(dest/'request.json',req)
        rows.append({'id':row['id'],'dataset':row['dataset'],'qualified':n+8192<=40960,'input_tokens':n,
            'request':str((dest/'request.json').relative_to(ROOT)),'ordered_card_roundtrip':decode(text)==evidence['cards'],
            'card_count':len(evidence['cards']),'evidence_sha256':__import__('hashlib').sha256(text.encode()).hexdigest()})
    report={'status':'passed' if all(r['qualified'] and r['ordered_card_roundtrip'] for r in rows) else 'failed',
        'rows':rows,'cases':len(rows),'new_calls':0,'no_truncation':True,'scope':'semantic_HTML_not_raw_web_source','with_plot_program':with_program,
        'source_sha256':__import__('RQs.RQ4_3.src.utils',fromlist=['digest']).digest(ROOT/'src/renderer/semantic_html.py'),
        'maximum_input_tokens':max(r['input_tokens'] for r in rows),
        'qualified':dict(Counter(r['dataset'] for r in rows if r['qualified']))}
    save(folder/'report.json',report);return report
