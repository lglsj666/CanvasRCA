"""Deterministic RQ4.1 integrity, token-support and bounded measurement helpers."""
import hashlib
import json
import math
import os
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def uniform_indices(size, divisor):
    if size < 1 or divisor < 1:
        raise ValueError("positive visual size and divisor required")
    count = math.ceil(size / divisor)
    if count == 1:
        return [0]
    return [round(i * (size - 1) / (count - 1)) for i in range(count)]


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def leaves(value, prefix=''):
    """Every occurrence including empty containers; no value deduplication."""
    if isinstance(value, dict) and value:
        for key, v in value.items():
            yield from leaves(v, prefix + '/' + str(key).replace('~', '~0').replace('/', '~1'))
    elif isinstance(value, list) and value:
        for i, v in enumerate(value):
            yield from leaves(v, prefix + '/' + str(i))
    else:
        yield prefix, value


def decode_sequence(value):
    if isinstance(value, list):
        return value
    if set(value) != {'length', 'value_positions'}:
        raise ValueError('Unknown sequence codec')
    sentinel = object()
    out = [sentinel] * value['length']
    for reading, positions in value['value_positions']:
        for span in positions.split(','):
            bounds = [int(v) for v in span.split('-')]
            if len(bounds) not in (1, 2):
                raise ValueError('Invalid run')
            for i in range(bounds[0], bounds[-1] + 1):
                if i < 0 or i >= len(out) or out[i] is not sentinel:
                    raise ValueError('Overlapping/out-of-range run')
                out[i] = reading
    if any(v is sentinel for v in out):
        raise ValueError('Incomplete sequence')
    return out


def physical_cores(limit=8):
    """Pin to distinct physical cores; never assume logical IDs are physical."""
    allowed = os.sched_getaffinity(0)
    result, seen = [], set()
    for cpu in sorted(allowed):
        base = Path(f'/sys/devices/system/cpu/cpu{cpu}/topology')
        key = ((base/'physical_package_id').read_text().strip(), (base/'core_id').read_text().strip())
        if key not in seen:
            seen.add(key); result.append(cpu)
        if len(result) == limit:
            break
    return result


def foreground_support(directory, processed_size, policy='exclusive_v1'):
    """Actual antialiased glyph support under the processor's affine resize.

    Palette decoding uncertainty is bounded per pixel using alpha and DOM
    geometry. No rectangular empty space becomes foreground. Lower/upper
    overlap areas distinguish a definite lost operand from a decoding doubt.
    This needs neither model weights nor invented encoder features.
    """
    import numpy as np
    from PIL import Image
    if policy not in {'exclusive_v1','shared_v2'}:raise ValueError('Unknown support policy')
    directory=Path(directory);audit=read_json(directory/'foreground_audit.json')
    if audit['issues']:raise ValueError('Foreground renderer audit failed')
    rgba=np.asarray(Image.open(directory/'role_foreground.png').convert('RGBA'))
    anch=np.asarray(Image.open(directory/'anchor_foreground.png').getchannel('A'))
    h,w=anch.shape;pw,ph=processed_size
    if pw%32 or ph%32:raise ValueError('Qwen post-merger grid must align to32 pixels')
    gw,gh=pw//32,ph//32;n=gw*gh;sx,sy=gw/w,gh/h
    def areas(xs,ys,weights):
        # Exact intersections of a transformed source-pixel square with grid
        # cells, not just its center. The common resize-area factor cancels.
        xf=xs*sx;yf=ys*sy;x0=np.floor(xf).astype(int);y0=np.floor(yf).astype(int)
        fx=np.minimum(1.,(x0+1-xf)/sx);fy=np.minimum(1.,(y0+1-yf)/sy)
        out=np.zeros(n,dtype=np.float64)
        for dx,wx in ((0,fx),(1,1-fx)):
            for dy,wy in ((0,fy),(1,1-fy)):
                weight=weights*wx*wy;valid=(weight>1e-12)&(x0+dx<gw)&(y0+dy<gh)
                out+=np.bincount((y0[valid]+dy)*gw+x0[valid]+dx,weights=weight[valid],minlength=n)
        return out
    ys,xs=np.nonzero(anch);anchor=areas(xs,ys,np.ones(len(xs)))>0
    ids=sorted(audit['palette']);lower=[];upper=[];nominal=[]
    for rid in ids:
        pixels={}
        color=np.asarray(audit['palette'][rid],dtype=float)
        for bx,by,bw,bh in audit['boxes'][rid]:
            x0=max(0,int(np.floor(bx))-4);x1=min(w,int(np.ceil(bx+bw))+4)
            y0=max(0,int(np.floor(by))-4);y1=min(h,int(np.ceil(by+bh))+4)
            crop=rgba[y0:y1,x0:x1];yy,xx=np.nonzero(crop[:,:,3])
            if not len(xx):continue
            rgb=crop[yy,xx,:3].astype(float);alpha=crop[yy,xx,3].astype(float)
            err=np.max(abs(rgb-color),axis=1)
            # Unpremultiplication may amplify one-channel rounding at tiny
            # alpha. Bounds include those pixels; only high-confidence ink
            # supplies a lower bound. Palette spacing is12 per channel.
            possible=err<=255/alpha+2
            for x,y,a,e in zip(xx[possible]+x0,yy[possible]+y0,alpha[possible],err[possible],strict=True):
                pixels[int(y)*w+int(x)]=(a,e)
        index=np.asarray(list(pixels),dtype=np.int64)
        values=np.asarray(list(pixels.values()),dtype=float).reshape(-1,2)
        ys=index//w;xs=index%w
        upper.append(areas(xs,ys,np.minimum(1,(values[:,0]+1)/255)))
        certain=(values[:,0]>=128)&(values[:,1]<=2)
        lower.append(areas(xs[certain],ys[certain],np.maximum(0,(values[certain,0]-1)/255)))
        estimate=np.minimum(1,values[:,0]/255)
        nominal.append(areas(xs,ys,estimate))
    lo=np.asarray(lower);hi=np.asarray(upper);estimate=np.asarray(nominal)
    winner=np.argmax(estimate,axis=0);occupied=estimate.max(axis=0)>0
    ambiguity=(hi>0).sum(axis=0)>1
    strongest=np.argmax(lo,axis=0);first=lo.max(axis=0)
    second=np.partition(lo,-2,axis=0)[-2] if len(ids)>1 else np.zeros(n)
    roles={};definite=[];ambiguous_empty=[];old_lost=[];uncertain_only=[]
    for i,rid in enumerate(ids):
        exclusive=np.flatnonzero(occupied&~anchor&(winner==i)).tolist()
        possible=hi[i]>0;fully=bool(possible.any() and not (possible&~anchor).any())
        support=np.flatnonzero(possible&~anchor).tolist() if policy=='shared_v2' else exclusive
        confirmed=np.flatnonzero((lo[i]>0)&~anchor).tolist()
        if support and not confirmed:uncertain_only.append(rid)
        # A role cannot win even with ALL its uncertain ink if another role
        # has strictly more certain ink at every non-anchor candidate token.
        competitor=np.where(strongest==i,second,first)
        impossible=bool((possible&~anchor).any() and np.all(competitor[possible&~anchor]>hi[i,possible&~anchor]+1e-9))
        if not exclusive and not fully:old_lost.append(rid)
        if not support and not fully:
            (definite if impossible else ambiguous_empty).append(rid)
        toks=np.flatnonzero(possible)
        if len(toks):
            x=toks%gw;y=toks//gw;bbox=float((x.max()-x.min()+1)**2+(y.max()-y.min()+1)**2)
        else:bbox=2.
        roles[rid]={'tokens':support,'fully_anchored':fully,'bbox_diag2':bbox,'patch_diag2':2.,
                    'foreground_possible_tokens':toks.tolist(),'definitely_lost_to_other_roles':impossible,
                    'confirmed_optional_tokens':confirmed,
                    'uncertain_only_tokens':sorted(set(support)-set(confirmed)),
                    'certain_area':float(lo[i].sum()),'possible_area':float(hi[i].sum()),
                    'loss_witness':[{'token':int(t),'other_role':ids[int(strongest[t])],
                                     'other_certain_area':float(competitor[t]),'own_possible_area':float(hi[i,t])}
                                    for t in np.flatnonzero(possible&~anchor)] if impossible else []}
        if policy=='shared_v2':
            roles[rid]['exclusive_v1_counterfactual']={'tokens':exclusive,
                'definitely_lost_to_other_roles':roles[rid].pop('definitely_lost_to_other_roles'),
                'loss_witness':roles[rid].pop('loss_witness')}
    shared=((hi>0).sum(axis=0)>1)&~anchor
    return {'schema':'CanonicalTokenSupportV2' if policy=='shared_v2' else 'CanonicalTokenSupportV1',
            'support_policy':policy,'roles':roles,'anchors':np.flatnonzero(anchor).tolist(),
            'image_tokens':n,'grid':[gh,gw],'processed_pixels':[pw,ph],
            'definite_empty_unanchored_roles':definite,'uncertain_empty_unanchored_roles':ambiguous_empty,
            'ambiguous_tokens':int(ambiguity.sum()),'foreground_union_tokens':int((occupied|anchor).sum()),
            'shared_nonanchor_tokens':int(shared.sum()),'max_roles_per_token':int((hi>0).sum(axis=0).max()),
            'role_token_incidences':sum(len(r['tokens']) for r in roles.values()),
            'uncertain_only_unanchored_roles':uncertain_only,
            'legacy_empty_roles':old_lost,
            'area_definition':'actual alpha foreground; exact affine pixel intersections; conservative decoding bounds',
            'requires_feature_extraction':False}


def source_order(rows):
    pending = list(rows); output = []
    while pending:
        selected, used = [], set()
        for row in pending:
            key = (row['dataset'], row.get('source', ''))
            if key not in used and len(selected) < 8:
                selected.append(row); used.add(key)
        for row in selected:
            pending.remove(row)
        output.extend(selected)
    return output


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


def coefficients(edges):
    from collections import Counter, defaultdict
    counts = Counter(e['type'] for e in edges)
    if not counts:
        raise ValueError('Empty comparison graph')
    out = defaultdict(float)
    for e in edges:
        if not e['roles'] or len(set(e['roles'])) != len(e['roles']):
            raise ValueError('Duplicate/empty role in edge')
        w = 1 / (len(counts) * counts[e['type']] * len(e['roles']))
        for u in e['roles']:
            out[(u, e['type'])] += w
    return dict(out)


def objective(quality, edges, unary=False):
    from collections import Counter
    counts = Counter(e['type'] for e in edges)
    if not counts:
        raise ValueError('Empty comparison graph')
    return sum((sum(quality[u] for u in e['roles'])/len(e['roles']) if unary
                else min(quality[u] for u in e['roles'])) / (len(counts)*counts[e['type']]) for e in edges)


def quota_targets(capacities, budget):
    """Capped proportional largest remainder; input order cannot affect ties."""
    if budget<0 or any(type(v) is not int or v<0 for v in capacities.values()):
        raise ValueError('Invalid quota capacity or budget')
    total=sum(capacities.values());budget=min(budget,total)
    if not total:return {u:0 for u in capacities}
    base={u:(budget*c)//total for u,c in capacities.items()}
    remain=budget-sum(base.values())
    order=sorted(capacities,key=lambda u:(-(budget*capacities[u]%total),u))
    for u in order[:remain]:base[u]+=1
    if any(base[u]>capacities[u] for u in base):raise AssertionError('Quota cap violated')
    return base


def isolated_glyph_tokens(path, processed_size):
    """Unambiguous alpha mask from ONE registered role via unified renderer."""
    import numpy as np
    from PIL import Image
    alpha=np.asarray(Image.open(path).getchannel('A'));h,w=alpha.shape;pw,ph=processed_size
    if pw%32 or ph%32:raise ValueError('Non-integral processor merger grid')
    gw,gh=pw//32,ph//32
    if gw>w or gh>h:raise ValueError('Unsupported greater-than-one token per source pixel')
    ys,xs=np.nonzero(alpha)
    x0=np.floor(xs*gw/w).astype(int);y0=np.floor(ys*gh/h).astype(int)
    x1=np.ceil((xs+1)*gw/w).astype(int)-1;y1=np.ceil((ys+1)*gh/h).astype(int)-1
    indices=np.concatenate([y*gw+x for x in (x0,x1) for y in (y0,y1)])
    if (indices<0).any() or (indices>=gw*gh).any():raise ValueError('Alpha support outside actual grid')
    return sorted(set(indices.tolist()))


def support_saturation(roles, anchors, n, fraction):
    """Feature-independent feasibility witness for objective1, NOT model masks."""
    a=set(anchors);union=a|{t for r in roles.values() for t in r['tokens']}
    empty=[u for u,r in roles.items() if not r['tokens'] and not r.get('fully_anchored')]
    if not 0<fraction<=1 or not union<=set(range(n)):raise ValueError('Invalid saturation audit')
    k=math.ceil(n*fraction)
    return {'budget':k,'unique_support_union':len(union),'anchor_feasible':len(a)<=k,
            'all_support_fits':not empty and len(union)<=k,
            'objective_one_feasible_in_exact_arithmetic':not empty and len(union)<=k,
            'empty_roles':empty,'actual_heuristic_masks_measured':False}


def evidence_budget(roles, anchors, n, fraction=.5, policy='grid_v2'):
    """Budget domain is explicit; E50 never means half of the original grid."""
    a=set(anchors);e={int(t) for r in roles.values() for t in r['tokens']}
    if not 0<fraction<=1 or a&e or not (a|e)<=set(range(n)):raise ValueError('Budget domain')
    if policy=='grid_v2':k=math.ceil(n*fraction);eligible=set(range(n))-a
    elif policy=='optional_support_v3':k=len(a)+math.ceil(len(e)*fraction);eligible=e
    else:raise ValueError('Unknown budget policy')
    if len(a)>k:raise ValueError('Anchor budget infeasible')
    return {'policy':policy,'total_tokens':k,'anchor_tokens':len(a),'optional_support_tokens':len(e),
        'optional_slots':k-len(a),'original_tokens':n,'actual_grid_fraction':k/n,'eligible':sorted(eligible),
        'all_support_fits':len(a|e)<=k}


def select_registered_condition(config, condition, features, xy, roles, anchors, edges, **kwargs):
    """Active matched-arm dispatch; legacy grid names never silently reappear."""
    if config.get('budget_policy')!='optional_support_v3' or condition not in config['conditions']:
        raise ValueError('Unregistered allocation condition')
    modes={'CVC':'CVC','REWIRED':'REWIRED','UNARY':'UNARY','QUOTA':'QUOTA','A_UNIFORM':'UNIFORM','A_DIVERSITY':'DIVERSITY'}
    if '_E' not in condition:raise ValueError('Condition does not use a matched allocator')
    name,ratio=condition.rsplit('_E',1)
    if name not in modes or ratio not in {'25','50','75'}:raise ValueError('Prior/native arm requires its own qualified adapter')
    if any(k in kwargs for k in ('budget_policy','mode','fraction')):raise ValueError('Registered budget cannot be overridden')
    return select_tokens(features,xy,roles,anchors,edges,int(ratio)/100,modes[name],budget_policy='optional_support_v3',**kwargs)


def rewire_covariates(provenance, support, features, xy, image_area):
    """Outcome-free metadata for the registered covariance-matched swap."""
    import numpy as np
    f=np.asarray(features,dtype=np.float32);norm=np.linalg.norm(f,axis=1)
    f=f/np.where(norm==0,1,norm)[:,None];out={}
    for role in provenance['roles']:
        u=role['id'];r=support['roles'][u];ids=r['foreground_possible_tokens']
        if not ids:raise ValueError('Missing canonical role')
        z=f[ids];center=np.asarray(xy)[ids].mean(axis=0)
        out[u]={'area':r['possible_area']/image_area,'dispersion':float(((z-z.mean(0))**2).sum(1).mean()),
                'center':center.tolist(),'signature':[role['quantity'],role['unit'],role['phase']]}
    return out


def bundle_distance(edge, covariates, diagonal):
    import math
    from itertools import combinations
    points=[covariates[u]['center'] for u in edge['roles']]
    distances=[math.dist(a,b)/diagonal for a,b in combinations(points,2)]
    return sum(distances)/len(distances) if distances else 0.


def fit_rewire_bins(cases):
    from collections import defaultdict
    samples=defaultdict(list)
    for case in cases:
        for edge in case['edges']:
            if len(edge['roles'])<2:continue
            t=edge['type']
            for j,u in enumerate(edge['roles']):
                for field in ('area','dispersion'):samples[f'{t}/{j}/{field}'].append(case['covariates'][u][field])
            samples[t+'/distance'].append(bundle_distance(edge,case['covariates'],case['diagonal']))
    return {k:[sorted(v)[math.floor((len(v)-1)*q)] for q in (1/3,2/3)] for k,v in sorted(samples.items())}


def matched_rewire(edges, covariates, bins, diagonal, seed):
    """Single deterministic stream; preserve degrees and reject original edges."""
    import numpy as np
    from collections import Counter,defaultdict
    current=[{'type':e['type'],'roles':list(e['roles'])} for e in sorted(edges,key=lambda e:(e['type'],tuple(e['roles'])))]
    def key(e):return (e['type'],tuple(sorted(e['roles'])))
    original={key(e) for e in current};present=set(original)
    if len(original)!=len(current):raise ValueError('Duplicate original edges')
    def bin_id(name,value):return int(np.searchsorted(bins[name],value,side='left'))
    groups=defaultdict(list)
    for i,e in enumerate(current):
        if len(e['roles'])>1:groups[e['type']].append(i)
    original_dist={i:bin_id(e['type']+'/distance',bundle_distance(e,covariates,diagonal)) for ids in groups.values() for i in ids for e in [current[i]]}
    report={};rng=np.random.default_rng(seed)
    for kind,ids in sorted(groups.items()):
        counts=Counter();m=len(ids)
        for _ in range(100*m if m>=2 else 0):
            counts['proposals']+=1;i,j=map(int,rng.choice(ids,size=2,replace=False));a,b=current[i],current[j]
            if len(a['roles'])!=len(b['roles']):counts['arity']+=1;continue
            pos=int(rng.integers(len(a['roles'])));u,v=a['roles'][pos],b['roles'][pos]
            if u==v:counts['unchanged']+=1;continue
            cu,cv=covariates[u],covariates[v]
            if cu['signature']!=cv['signature']:counts['signature']+=1;continue
            if any(bin_id(f'{kind}/{pos}/{f}',cu[f])!=bin_id(f'{kind}/{pos}/{f}',cv[f]) for f in ('area','dispersion')):
                counts['operand_bin']+=1;continue
            aa={'type':kind,'roles':list(a['roles'])};bb={'type':kind,'roles':list(b['roles'])}
            aa['roles'][pos],bb['roles'][pos]=v,u;ka,kb=key(aa),key(bb)
            if len(set(aa['roles']))!=len(aa['roles']) or len(set(bb['roles']))!=len(bb['roles']):counts['self']+=1;continue
            if ka in original or kb in original or ka in present or kb in present or ka==kb:counts['duplicate_or_original']+=1;continue
            if (bin_id(kind+'/distance',bundle_distance(aa,covariates,diagonal))!=original_dist[i] or
                bin_id(kind+'/distance',bundle_distance(bb,covariates,diagonal))!=original_dist[j]):counts['distance_bin']+=1;continue
            present.remove(key(a));present.remove(key(b));present.update([ka,kb]);current[i],current[j]=aa,bb;counts['accepted']+=1
        report[kind]=dict(counts)
    if coefficients(edges)!=coefficients(current):raise AssertionError('Degree-derived coefficients changed')
    return current,{'types':report,'graph_changed':present!=original,'edge_symmetric_difference':len(present^original),
        'unary_coefficients_equal':True,'seed':int(seed),'bins_scope':'provided cohort, no automatic full-roster claim'}


def audit_selected_quality(features, xy, roles, selected, reported, tolerance=2e-6):
    """Independent FP64 distances to retained tokens, without greedy caches."""
    import numpy as np
    keep=set(selected);reference={}
    for u,r in roles.items():
        ids=list(r['tokens']);retained=[i for i,t in enumerate(ids) if t in keep]
        if not ids:
            if not r.get('fully_anchored'):raise ValueError('Unanchored empty audit role')
            reference[u]=1.;continue
        if not retained:reference[u]=0.;continue
        x=np.asarray(features[ids],dtype=np.float64);n=np.sqrt(np.sum(x*x,axis=1))
        x=x/np.where(n==0,1,n)[:,None];p=np.asarray(xy,dtype=np.float64)[ids]
        d=((p[:,None,:]-p[retained][None,:,:])**2).sum(axis=-1)
        z=1-.25*(1-np.clip(x@x[retained].T,-1,1))-.5*np.minimum(1,d/max(r['bbox_diag2'],r['patch_diag2']))
        for j,i in enumerate(retained):z[i,j]=1.
        reference[u]=float(np.clip(z,0,1).max(axis=1).mean())
    if set(reference)!=set(reported):raise ValueError('Quality role set changed')
    error=max((abs(reference[u]-reported[u]) for u in reference),default=0.)
    if not math.isfinite(error) or error>tolerance:raise ValueError('Independent quality recomputation mismatch '+str(error))
    return {'status':'passed','max_absolute_error':error,'tolerance':tolerance,'roles':len(reference)}


def visual_gather_plan(input_ids, position_ids, attention_mask, image_token_id, selected):
    """CPU index plan preserving native MRoPE coordinates and all valid text."""
    import numpy as np
    ids=np.asarray(input_ids);pos=np.asarray(position_ids);mask=np.asarray(attention_mask)
    if ids.ndim!=1 or pos.shape!=(3,len(ids)) or mask.shape!=ids.shape or not np.isin(mask,[0,1]).all():
        raise ValueError('Malformed native input geometry')
    visual=np.flatnonzero((ids==image_token_id)&(mask==1));selected=list(selected)
    if any(not isinstance(v,(int,np.integer)) or isinstance(v,bool) for v in selected):raise ValueError('Noninteger selected position')
    if selected!=sorted(set(selected)) or any(v<0 or v>=len(visual) for v in selected):raise ValueError('Invalid selected visual positions')
    retained=(mask==1)&(ids!=image_token_id);retained[visual[selected]]=True;index=np.flatnonzero(retained)
    if not len(index):raise ValueError('Empty diagnostic request')
    next_position=int(pos[:,mask==1].max())+1
    return {'retained_input_indices':index,'retained_position_ids':pos[:,index],
            'original_visual_positions':visual,'selected_visual_indices':np.asarray(selected,dtype=np.int64),
            'text_tokens':int(((mask==1)&(ids!=image_token_id)).sum()),'input_tokens':len(index),
            'next_text_position':next_position,'rope_delta_after_gather':next_position-len(index)}


def audit_rewired_graph(original, rewired, covariates, bins, diagonal):
    """Check final invariants independently from the swap acceptance loop."""
    from collections import Counter
    from itertools import combinations
    ordered=sorted(original,key=lambda e:(e['type'],tuple(e['roles'])))
    if len(ordered)!=len(rewired):raise ValueError('Changed number of dependency edges')
    degrees=lambda es:Counter((e['type'],j,u) for e in es for j,u in enumerate(e['roles']))
    if degrees(ordered)!=degrees(rewired):raise ValueError('Role/type/position degree changed')
    def cell(name,v):return sum(v>x for x in bins[name])
    def distance(e):
        pairs=list(combinations(e['roles'],2))
        return sum(math.sqrt(sum((a-b)**2 for a,b in zip(covariates[u]['center'],covariates[v]['center'])))/diagonal for u,v in pairs)/len(pairs) if pairs else 0.
    keys=[(e['type'],tuple(sorted(e['roles']))) for e in rewired]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate rewired edge')
    for before,after in zip(ordered,rewired,strict=True):
        kind=before['type']
        if after['type']!=kind or len(before['roles'])!=len(after['roles']):raise ValueError('Dependency type/arity changed')
        if len(after['roles'])!=len(set(after['roles'])):raise ValueError('Repeated role within edge')
        for j,(u,v) in enumerate(zip(before['roles'],after['roles'],strict=True)):
            if covariates[u]['signature']!=covariates[v]['signature']:raise ValueError('Operand signature changed')
            if len(before['roles'])>1:
                for f in ('area','dispersion'):
                    if cell(f'{kind}/{j}/{f}',covariates[u][f])!=cell(f'{kind}/{j}/{f}',covariates[v][f]):raise ValueError('Operand bin changed')
        if len(before['roles'])>1 and cell(kind+'/distance',distance(before))!=cell(kind+'/distance',distance(after)):
            raise ValueError('Original edge distance bin changed')
    return {'status':'passed','edges':len(ordered),'role_type_position_degrees_equal':True,'operand_signature_and_bins_equal':True,'each_original_distance_bin_equal':True}


def select_tokens(features, xy, roles, anchors, edges, fraction=.5, mode='CVC', seconds=30, trace=False,
                  budget_policy='grid_v2', engine='incremental_v3'):
    """Shared-support greedy; unique token cost and simultaneous actual gains.

    FP32 per-role coverage, sparse affected-edge updates, bounded similarities.
    Overlap updates ALL incident roles; no token copy or duplicated charge.
    """
    import numpy as np
    import time
    import heapq
    from collections import Counter,defaultdict
    began=time.monotonic();f=np.asarray(features,dtype=np.float32);xy=np.asarray(xy,dtype=np.float32)
    if f.ndim!=2 or not len(f) or xy.shape!=(len(f),2) or not np.isfinite(f).all() or not np.isfinite(xy).all():
        raise ValueError('Feature/geometry contract')
    if mode not in {'CVC','REWIRED','UNARY','QUOTA','UNIFORM','DIVERSITY'}:raise ValueError('Unsupported selector')
    if engine not in {'exhaustive_v2','incremental_v3'}:raise ValueError('Unknown exact search engine')
    n=len(f);plan=evidence_budget(roles,anchors,n,fraction,budget_policy);k=plan['total_tokens'];selected=set(anchors)
    domain_mask=np.zeros(n,dtype=bool);domain_mask[plan['eligible']]=True
    if not 0<fraction<=1 or len(selected)>k or not selected<=set(range(n)):
        raise ValueError('Anchor budget infeasible')
    normalized={}
    for u,r in sorted(roles.items()):
        if any(not isinstance(t,(int,np.integer)) or isinstance(t,bool) for t in r['tokens']):raise ValueError('Noninteger role token')
        ids=sorted({int(t) for t in r['tokens']})
        if not set(ids)<=set(range(n)) or set(ids)&selected:raise ValueError('Out-of-range or anchor in optional support')
        if not ids and not r.get('fully_anchored'):raise ValueError('Empty unanchored role')
        if ids and r.get('fully_anchored'):raise ValueError('Fully anchored role has optional tokens')
        normalized[u]={**r,'tokens':ids}
    roles=normalized;edges=sorted(edges,key=lambda e:(e['type'],tuple(e['roles'])))
    coef=coefficients(edges)
    if {u for u,_ in coef}!=set(roles):raise ValueError('Graph must cover exactly the registered roles')
    needed=sum(len(r['tokens'])**2*16 for r in roles.values())+f.nbytes*3+xy.nbytes*2
    if mode=='DIVERSITY' and engine=='incremental_v3':needed+=int(domain_mask.sum())*f.shape[1]*4
    norms=np.linalg.norm(f,axis=1);f=f/np.where(norms==0,1,norms)[:,None]
    sims={};coverage={};quality={};locations=defaultdict(list);cache={}
    for u,r in roles.items():
        ids=np.asarray(r['tokens'],dtype=int)
        if not len(ids):quality[u]=1.;continue
        ff=f[ids];pp=xy[ids];distances=((pp[:,None,:]-pp[None,:,:])**2).sum(-1)
        denominator=max(float(r['bbox_diag2']),float(r['patch_diag2']))
        if not math.isfinite(denominator) or denominator<=0:raise ValueError('Nonpositive role geometry')
        sim=1-(.5*(1-np.clip(ff@ff.T,-1,1))/2+.5*np.minimum(1,distances/denominator))
        np.fill_diagonal(sim,1.);sims[u]=np.clip(sim,0,1)
        coverage[u]=np.zeros(len(ids),dtype=np.float32);quality[u]=0.
        for j,t in enumerate(ids):locations[int(t)].append((u,j))
    weights={u:sum(v for (r,_),v in coef.items() if r==u) for u in roles}
    counts=Counter(e['type'] for e in edges)
    edge_weights=[1/(len(counts)*counts[e['type']]) for e in edges]
    incidence=defaultdict(list)
    for e,edge in enumerate(edges):
        for u in edge['roles']:incidence[u].append(e)
    min_spatial=np.full(n,np.inf);min_feature=np.full(n,np.inf)
    taken=np.zeros(n,dtype=bool);taken[list(selected)]=True
    feature_domain=np.flatnonzero(domain_mask) if engine=='incremental_v3' else np.arange(n)
    feature_rows=f[feature_domain] if mode=='DIVERSITY' else None
    def update_feature_distance(t):
        # Only eligible candidates can ever be selected. Compute the SAME
        # per-row cosine on that domain; do not scan unused image background
        # once for each mandatory anchor. Dense reference remains auditable.
        min_feature[feature_domain]=np.minimum(min_feature[feature_domain],1-np.clip(feature_rows@f[t],-1,1))
    for t in sorted(selected):
        min_spatial=np.minimum(min_spatial,((xy-xy[t])**2).sum(1))
        if mode=='DIVERSITY':update_feature_distance(t)
    def spatial_next():
        remaining=np.flatnonzero(~taken&domain_mask)
        if not selected:return int(remaining[np.argmin(((xy[remaining]-xy.mean(0))**2).sum(1))])
        return int(remaining[np.argmax(min_spatial[remaining])])
    def qualities_after(action):
        touched=defaultdict(list)
        for t in action:
            for u,j in locations.get(t,[]):touched[u].append(j)
        updates={}
        for u,columns in touched.items():
            if len(columns)==1 and u in cache:updates[u]=float(cache[u][columns[0]])
            else:updates[u]=float(np.maximum(coverage[u],sims[u][:,columns].max(axis=1)).mean(dtype=np.float32))
        return updates
    def action_gains(action):
        updates=qualities_after(action)
        ug=sum(weights[u]*(v-quality[u]) for u,v in updates.items())
        if mode=='UNARY':return ug,ug
        affected={i for u in updates for i in incidence[u]}
        delta=sum(edge_weights[i]*(min(updates.get(u,quality[u]) for u in edges[i]['roles'])-
            min(quality[u] for u in edges[i]['roles'])) for i in sorted(affected))
        return delta,ug
    def refresh():
        for u,sim in sims.items():
            # Reduce each candidate's contiguous role vector identically to
            # committed coverage, avoiding row/column FP32 summation drift.
            if u not in cache:cache[u]=np.maximum(coverage[u][:,None],sim).T.copy().mean(axis=1,dtype=np.float32)
    def best_for_role(u):
        columns=[j for j,t in enumerate(roles[u]['tokens']) if not taken[t]]
        if not columns:return None
        j=min(columns,key=lambda j:(-float(cache[u][j]),roles[u]['tokens'][j]))
        return roles[u]['tokens'][j]
    actions_trace=[];quota={u:0 for u in roles};credits={u:0 for u in roles}
    # Exact incremental enumeration. A changed q/coverage can change single
    # gains only for tokens supporting that role or a role in an incident edge.
    affected_tokens={u:set(r['tokens']) for u,r in roles.items()}
    if mode!='UNARY':
        for edge in edges:
            tokens={t for u in edge['roles'] for t in roles[u]['tokens']}
            for u in edge['roles']:affected_tokens[u].update(tokens)
    dirty=set(locations);heap=[];versions={};single_ranks={};positive=set()
    while len(selected)<k:
        if time.monotonic()-began>seconds:raise TimeoutError('Selector exceeded per-case CPU time bound')
        if mode=='UNIFORM':action=(spatial_next(),)
        elif mode=='DIVERSITY':
            remaining=np.flatnonzero(~taken&domain_mask)
            action=(spatial_next() if not selected else int(remaining[np.argmax(min_feature[remaining])]),)
        else:
            refresh()
            if mode=='QUOTA':
                capacity={u:sum(not taken[t] for t in r['tokens']) for u,r in roles.items()}
                eligible=[u for u in roles if credits[u]<quota[u] and capacity[u]]
                if not eligible and any(capacity.values()):
                    allocation=quota_targets(capacity,k-len(selected))
                    quota={u:credits[u]+allocation[u] for u in roles}
                    eligible=[u for u in roles if credits[u]<quota[u] and capacity[u]]
                if eligible:
                    u=min(eligible,key=lambda u:(-(quota[u]-credits[u]),u));action=(best_for_role(u),)
                else:action=(spatial_next(),)
            else:
                # Non-role singles have exactly zero primary/unary gain. They
                # participate through the identical zero-plateau FPS rule.
                if engine=='incremental_v3':
                    for t in sorted(dirty):
                        if taken[t]:
                            single_ranks.pop(t,None);positive.discard(t);continue
                        gain,ug=action_gains((t,));rank=(-gain,-gain,-ug,(t,))
                        versions[t]=versions.get(t,0)+1;single_ranks[t]=rank
                        heapq.heappush(heap,(rank,versions[t]))
                        if abs(gain)>1e-12 or abs(ug)>1e-12:positive.add(t)
                        else:positive.discard(t)
                    dirty.clear()
                    if len(heap)>8*max(1,len(single_ranks)):
                        heap=[(v,versions[t]) for t,v in single_ranks.items() if not taken[t]];heapq.heapify(heap)
                    while heap and (taken[heap[0][0][3][0]] or versions[heap[0][0][3][0]]!=heap[0][1]):heapq.heappop(heap)
                    best=heap[0][0] if heap else None;nonzero=bool(positive)
                    actions=set()
                else:
                    actions={(t,) for t in locations if not taken[t]};best=None;nonzero=False
                if mode in {'CVC','REWIRED'}:
                    for edge in edges:
                        if engine=='incremental_v3' and len(edge['roles'])==1:continue
                        minimum=min(quality[u] for u in edge['roles']);picks=[]
                        for u in edge['roles']:
                            if abs(quality[u]-minimum)<=1e-12:
                                pick=best_for_role(u)
                                if pick is not None:picks.append(pick)
                        if picks:actions.add(tuple(sorted(set(picks))))
                for a in sorted(actions):
                    if len(a)>k-len(selected):continue
                    gain,ug=action_gains(a)
                    nonzero|=abs(gain)>1e-12 or abs(ug)>1e-12
                    rank=(-gain/len(a),-gain,-ug,a)
                    if best is None or rank<best:best=rank
                action=best[3] if nonzero else (spatial_next(),)
        if len(set(action))!=len(action) or any(taken[t] for t in action):raise AssertionError('Duplicate token charge')
        before=objective(quality,edges,unary=mode=='UNARY') if trace else None
        # Apply the whole union once to every incident role. Recompute the
        # combined max; never sum overlapping single-token gains.
        touched=defaultdict(list)
        for t in action:
            selected.add(t);taken[t]=True
            min_spatial=np.minimum(min_spatial,((xy-xy[t])**2).sum(1))
            if mode=='DIVERSITY':update_feature_distance(t)
            for u,j in locations.get(t,[]):touched[u].append(j)
        for u,columns in touched.items():
            coverage[u]=np.maximum(coverage[u],sims[u][:,columns].max(axis=1))
            quality[u]=float(coverage[u].mean(dtype=np.float32));cache.pop(u,None);credits[u]+=len(columns)
            dirty.update(affected_tokens[u])
        dirty.update(action)
        if trace:actions_trace.append({'tokens':list(action),'cost':len(action),'affected_roles':sorted(touched),
            'gain':objective(quality,edges,unary=mode=='UNARY')-before,'quality':dict(quality)})
    result={'indices':sorted(selected),'quality':quality,'objective':objective(quality,edges),
            'unary':objective(quality,edges,True),'seconds':time.monotonic()-began,'working_bytes_bound':needed,
            'support_policy':'shared_v2','unique_token_cost':len(selected),'optional_incidences_covered':sum(credits.values())}
    result['budget']={k:v for k,v in plan.items() if k!='eligible'};result['engine']=engine
    if trace:result['actions']=actions_trace
    return result


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


def inventory_context_protection(manifest,grid,anchors,k,card_id='INV002'):
    """Keep the measured inventory region, with one merged-cell context margin.

    This consumes the original K, never computes a larger budget and never
    receives entity values, labels, model answers or a diagnostic ranking.
    """
    h,w=grid;source=manifest['source_png']
    rows=[b for b in manifest['audit']['bindings'] if b['key']==card_id+'.title' or b['key'].startswith(card_id+'.identity.')]
    if not rows or not any(b['key'].startswith(card_id+'.identity.') for b in rows):raise ValueError('Candidate inventory geometry absent')
    if any(not all(math.isfinite(b[z]) for z in ('x','y','width','height')) or b['width']<=0 or b['height']<=0 for b in rows):raise ValueError('Invalid inventory geometry')
    x0=max(0,math.floor(min(b['x'] for b in rows)*w/source['width'])-1)
    x1=min(w,math.ceil(max(b['x']+b['width'] for b in rows)*w/source['width'])+1)
    y0=max(0,math.floor(min(b['y'] for b in rows)*h/source['height'])-1)
    y1=min(h,math.ceil(max(b['y']+b['height'] for b in rows)*h/source['height'])+1)
    rectangle={y*w+x for y in range(y0,y1) for x in range(x0,x1)}
    original=set(protected_visual_indices(anchors,h*w,k))
    selected=protected_visual_indices(sorted(original|rectangle),h*w,k)
    return {'schema':'InventoryContextProtectionV1','policy':'inventory_context_v24',
        'protected_indices':selected,'original_anchor_count':len(original),'additional_cells':len(rectangle-original),
        'grid':list(grid),'rectangle_xyxy':[x0,y0,x1,y1],'fixed_original_K':k,'optional_slots_remaining':k-len(selected),
        'candidate_values_received':False}


def protected_visual_indices(values, n, k):
    """Validate public, image-side anchors without inventing model-visible IDs."""
    import numbers
    values=[] if values is None else list(values)
    if any(not isinstance(i,numbers.Integral) or isinstance(i,bool) for i in values):
        raise ValueError('Protected visual indices must be integers')
    result=sorted(set(map(int,values)))
    if len(result)!=len(values) or len(result)>k or any(i<0 or i>=n for i in result):
        raise ValueError('Invalid or over-budget protected visual indices')
    return result


def scope_select(features, saliency, k, seconds=30, protected=None):
    """SCOPE saliency-times-coverage, exact lazy greedy (alpha=1).

    Reference: kinredon/SCOPE@6bf7306, scope/clip_encoder.py::SCOPE.
    Actual attention-derived saliency is mandatory; a norm proxy is forbidden.
    Lazy upper bounds exploit diminishing marginal gains, not an approximation.
    """
    import heapq
    import time
    import numpy as np
    began=time.monotonic();f=np.asarray(features,dtype=np.float32);s=np.asarray(saliency,dtype=np.float64)
    if f.ndim!=2 or len(f)<1 or not np.isfinite(f).all():raise ValueError('SCOPE finite feature matrix required')
    n=len(f)
    if s.shape!=(n,) or not np.isfinite(s).all() or np.any(s<0) or not 1<=k<=n:raise ValueError('SCOPE attention/count')
    anchors=protected_visual_indices(protected,n,k)
    norms=np.linalg.norm(f,axis=1)
    if np.any(norms==0):raise ValueError('SCOPE reference has undefined zero-vector cosine')
    unit=f/norms[:,None];similarity=np.empty((n,n),np.float32);initial=np.empty(n,np.float64)
    for start in range(0,n,128):
        if time.monotonic()-began>seconds:raise TimeoutError('SCOPE CPU resource guard')
        block=unit[start:start+128]@unit.T;similarity[start:start+128]=block
        initial[start:start+128]=np.maximum(block,0).sum(axis=1,dtype=np.float64)*s[start:start+128]
    anchor_set=set(anchors)
    heap=[(-float(initial[i]),i,-1) for i in range(n) if i not in anchor_set];heapq.heapify(heap)
    coverage=np.zeros(n,np.float32);selected=list(anchors);evaluations=0
    for i in anchors:np.maximum(coverage,similarity[i],out=coverage)
    while len(selected)<k:
        if time.monotonic()-began>seconds:raise TimeoutError('SCOPE CPU resource guard')
        negative,i,stamp=heapq.heappop(heap)
        if stamp==len(selected):
            selected.append(i);np.maximum(coverage,similarity[i],out=coverage)
        else:
            gain=np.maximum(similarity[i]-coverage,0).sum(dtype=np.float64)*s[i];evaluations+=1
            heapq.heappush(heap,(-float(gain),i,len(selected)))
    return {'indices':sorted(selected),'selection_order':selected,'seconds':time.monotonic()-began,
            'target_k':k,'gain_evaluations':evaluations,'signal':'required_actual_attention','reference':'kinredon/SCOPE@6bf7306',
            'protected_indices':anchors,'protection_policy':'shared_anchors_v22' if anchors else 'none'}


def dart_select(hidden, keys, visual_positions, k, image_pivots=4, text_pivots=4):
    """DART K-L1 pivots and low-duplication selection on UPDATED states.

    Equal quotas reproduce official Qwen2.5 code when (K-Pv) is divisible by
    Pv+Pt. Remaining slots follow pivot iteration order, explicitly registered
    for exact arbitrary K. No CVC anchors or source metadata enter selection.
    hidden is the final-norm view of the pre-prune updated states; actual
    gathered decoder states remain unnormalized. keys are actual mixer keys.
    """
    import torch
    if hidden.ndim!=2 or keys.ndim!=2 or hidden.shape[0]!=keys.shape[0]:raise ValueError('DART states/keys')
    # CPU profiling favors512-row chunks; GPU keeps full vectorized operations.
    # No host-RAM cap or unmeasured CPU tradeoff is imposed on GPU execution.
    block_rows=512 if hidden.device.type=='cpu' else max(1,len(hidden))
    for matrix in (hidden,keys):
        if any(not torch.isfinite(matrix[i:i+block_rows]).all() for i in range(0,len(matrix),block_rows)):
            raise ValueError('DART nonfinite states')
    pos=torch.as_tensor(visual_positions,device=hidden.device,dtype=torch.long)
    if pos.ndim!=1 or not len(pos) or not torch.equal(pos,torch.arange(pos[0],pos[0]+len(pos),device=pos.device)):
        raise ValueError('DART requires one contiguous original image block')
    if int(pos[-1])>=len(hidden) or int(pos[0])<0 or not 1<=k<=len(pos):raise ValueError('DART image bounds/budget')
    tail=torch.arange(int(pos[-1])+1,len(hidden),device=hidden.device)
    pv=min(image_pivots,k,len(pos));pt=min(text_pivots,len(tail))
    if pv<1 or pt<0:raise ValueError('DART pivot counts')
    def key_norm(indices):
        return torch.cat([torch.norm(keys[indices[i:i+block_rows]],p=1,dim=-1) for i in range(0,len(indices),block_rows)])
    image=pos[key_norm(pos).topk(pv).indices].tolist()
    text=tail[key_norm(tail).topk(pt).indices].tolist() if pt else []
    pivots=list(set(image+text));remaining=set(pos.tolist())-set(image);selected=set(image)
    quota,remainder=divmod(k-pv,len(pivots));quotas=[]
    for j,pivot in enumerate(pivots):
        count=quota+int(j<remainder);quotas.append(count)
        if not count:continue
        candidates=list(remaining)
        # Same rowwise cosine; CPU chunks are retained for measured speed.
        score=torch.cat([-torch.nn.functional.cosine_similarity(hidden[pivot],hidden[candidates[i:i+block_rows]],dim=-1)
                         for i in range(0,len(candidates),block_rows)])
        chosen=[candidates[t] for t in score.topk(count).indices.tolist()]
        selected.update(chosen);remaining.difference_update(chosen)
    indices=sorted(i-int(pos[0]) for i in selected)
    if len(indices)!=k:raise RuntimeError('DART exact budget failed')
    return {'indices':indices,'image_pivots':image,'text_pivots':text,'pivot_order':pivots,
            'per_pivot_quotas':quotas,'target_k':k,'reference':'ZichenWen1/DART@0c88867'}


def s2prune_select(erc_scores, image, grid, k, coarse_grid=9, protected=None):
    """Published capped Laplacian allocation, recursive cells, max ERC.

    Reference: yuanyuanjia71-spec/S2Prune@b0ac197, allocation.py. Original
    fixed-576 budget grid is explicit at the caller; large Qwen grids use the
    preregistered 9x9 setting, not image resizing or outcome-selected grids.
    """
    import numpy as np
    score=np.asarray(erc_scores,dtype=np.float32).reshape(-1);h,w=map(int,grid)
    if h<1 or w<1 or len(score)!=h*w or not np.isfinite(score).all() or np.any(score<0):raise ValueError('S2Prune ERC/grid')
    if not 1<=coarse_grid<=min(h,w) or not coarse_grid**2<=k<=h*w:raise ValueError('S2Prune grid/budget')
    anchors=protected_visual_indices(protected,h*w,k);anchor_set=set(anchors)
    re=[round(i*h/coarse_grid) for i in range(coarse_grid+1)];ce=[round(i*w/coarse_grid) for i in range(coarse_grid+1)]
    regions=[(re[i],re[i+1],ce[j],ce[j+1]) for i in range(coarse_grid) for j in range(coarse_grid)]
    gray=np.asarray(image.convert('L'),np.float32)
    if min(gray.shape)<3:raise ValueError('S2Prune Laplacian image too small')
    pad=np.pad(gray,1,mode='edge');lap=pad[:-2,1:-1]+pad[2:,1:-1]+pad[1:-1,:-2]+pad[1:-1,2:]-4*gray
    ih,iw=gray.shape
    raw=np.array([np.var(lap[round(a*ih/h):round(b*ih/h),round(c*iw/w):round(d*iw/w)],dtype=np.float64)
                  for a,b,c,d in regions],np.float32)
    if not np.isfinite(raw).all():raise ValueError('S2Prune empty/nonfinite Laplacian region')
    complexity=(raw-raw.min())/max(float(raw.max()-raw.min()),np.finfo(np.float32).eps)
    required=np.array([sum(y*w+x in anchor_set for y in range(a,b) for x in range(c,d)) for a,b,c,d in regions]) if anchors else np.zeros(len(regions),dtype=int)
    capacity=np.array([(b-a)*(d-c) for a,b,c,d in regions])-required
    optional=k-len(anchors)
    allocation=(capacity>0).astype(int) if optional>=int((capacity>0).sum()) else np.zeros(len(regions),dtype=int)
    remaining=optional-int(allocation.sum())
    while remaining:
        available=capacity-allocation;eligible=np.flatnonzero(available>0);before=eligible.copy()
        weights=complexity[eligible].astype(np.float64)
        if weights.sum()<=np.finfo(np.float64).eps:weights.fill(1)
        quota=weights/weights.sum()*remaining;add=np.minimum(np.floor(quota).astype(int),available[eligible])
        allocation[eligible]+=add;remaining-=int(add.sum())
        if not remaining:break
        fractions=dict(zip(before.tolist(),(quota-np.floor(quota)).tolist()))
        order=sorted(np.flatnonzero(capacity-allocation>0).tolist(),key=lambda i:(fractions.get(i,0),complexity[i],-i),reverse=True)
        for i in order:
            if not remaining:break
            allocation[i]+=1;remaining-=1
    final=[];chosen=list(anchors)
    for region,budget in zip(regions,allocation):
        if not budget:continue
        cells=[region]
        def available(cell):
            a,b,c,d=cell
            return [y*w+x for y in range(a,b) for x in range(c,d) if y*w+x not in anchor_set]
        while len(cells)<budget:
            _,i,a,b,c,d=min((-(b-a)*(d-c),i,a,b,c,d) for i,(a,b,c,d) in enumerate(cells)
                          if (len(available((a,b,c,d)))>1 if anchors else b-a>1 or d-c>1))
            if b-a>=d-c and b-a>1:
                mid=a+(b-a)//2;parts=[(a,mid,c,d),(mid,b,c,d)]
            else:
                mid=c+(d-c)//2;parts=[(a,b,c,mid),(a,b,mid,d)]
            cells[i:i+1]=[cell for cell in parts if available(cell)] if anchors else parts
        final.extend(cells)
        for a,b,c,d in cells:
            ids=np.array(available((a,b,c,d))) if anchors else np.array([y*w+x for y in range(a,b) for x in range(c,d)])
            chosen.append(int(ids[np.argmax(score[ids])]))
    if len(set(chosen))!=k:raise RuntimeError('S2Prune exact budget failed')
    return {'indices':sorted(chosen),'regions':regions,'region_budgets':(allocation+required).tolist(),
            'final_cells':final,'raw_complexity':raw.tolist(),'normalized_complexity':complexity.tolist(),
            'target_k':k,'reference':'yuanyuanjia71-spec/S2Prune@b0ac197',
            'protected_indices':anchors,'protected_region_counts':required.tolist(),
            'optional_region_budgets':allocation.tolist(),'protection_policy':'shared_anchors_v22' if anchors else 'none'}


class ScopeVisionSignal:
    """Qwen-specific incoming-attention saliency; never a feature-norm proxy.

    Qwen has no CLS. Average real post-RoPE attention over patch queries and
    heads in the penultimate vision block, then sum within each merger group.
    This is a disclosed Qwen adaptation, not the released CLIP CLS signal.
    The normal forward/backend is untouched. Only the vector is retained.
    """
    def __init__(self, vision, chunk=32):
        if len(vision.blocks)<2 or chunk<1:raise ValueError('SCOPE requires a penultimate vision block')
        self.vision=vision;self.chunk=chunk;self.saliency=None;self.features=None;self.handles=[]

    def __enter__(self):
        block=self.vision.blocks[-2]
        self.handles=[block.attn.register_forward_pre_hook(self._capture,with_kwargs=True),
                      block.register_forward_hook(self._features)]
        return self

    def _capture(self,module,args,kwargs):
        import torch
        from transformers.models.qwen3_5.modeling_qwen3_5 import apply_rotary_pos_emb_vision
        x=args[0] if args else kwargs['hidden_states'];n=len(x)
        cuts=kwargs.get('cu_seqlens',args[1] if len(args)>1 else None)
        if cuts is None or cuts.tolist()!=[0,n]:raise ValueError('SCOPE registered single-image path only')
        with torch.no_grad():
            q,k,_=module.qkv(x).reshape(n,3,module.num_heads,-1).permute(1,0,2,3).unbind(0)
            cos,sin=kwargs['position_embeddings'];q,k=apply_rotary_pos_emb_vision(q,k,cos,sin)
            q=q.transpose(0,1).float();k=k.transpose(0,1).float();total=q.new_zeros(n)
            for start in range(0,n,self.chunk):
                probs=torch.softmax((q[:,start:start+self.chunk]@k.transpose(-1,-2))*module.scaling,dim=-1)
                total+=probs.sum(dim=(0,1))
            raw=total/(module.num_heads*n);merge=self.vision.spatial_merge_size**2
            if n%merge:raise ValueError('SCOPE merger group shape')
            self.saliency=raw.reshape(-1,merge).sum(-1).detach()

    def _features(self,module,args,output):
        merge=self.vision.spatial_merge_size**2
        self.features=output.detach().float().reshape(-1,merge,output.shape[-1]).mean(1)

    def __exit__(self,*exc):
        for handle in self.handles:handle.remove()
        self.handles=[]


def hybrid_prior_prefill(model, embeddings, position_ids, visual_positions, k,
                         method, image=None, grid=None, coarse_grid=9, fixed_selection=None,
                         use_cache=True, protected=None):
    """Single-call Qwen hybrid N->K prefill, preserving UPDATED hidden states.

    Early recurrent layers keep the state of the full prefix they consumed;
    later layers consume the shortened prefix. Recurrent state is not a token
    table and is never indexed on a guessed axis. This declared hybrid-model
    adaptation differs from S2Prune's released all-attention prefix-KV gather.
    CPU tests compare cached continuation with full layerwise recomputation.
    No checkpoint loading or generation happens in this helper.
    """
    import torch
    from transformers.cache_utils import DynamicCache
    from transformers.models.qwen3_5.modeling_qwen3_5 import create_causal_mask,create_recurrent_attention_mask
    if method not in ('DART','S2PRUNE'):raise ValueError('Unknown mid-decoder prior')
    boundary=2 if method=='DART' else 1
    if embeddings.ndim!=3 or embeddings.shape[0]!=1:raise ValueError('Registered prior adapter supports batch1 only')
    if position_ids.shape!=(4,1,embeddings.shape[1]):raise ValueError('Qwen four-axis positions required')
    if any(t!='linear_attention' for t in model.config.layer_types[:boundary]):raise ValueError('Different prefix cache architecture requires separate qualification')
    if len(model.layers)<=boundary:raise ValueError('No suffix layers')
    visual=torch.as_tensor(visual_positions,dtype=torch.long,device=embeddings.device)
    if visual.ndim!=1 or not len(visual) or not torch.equal(visual,torch.arange(visual[0],visual[0]+len(visual),device=visual.device)):
        raise ValueError('One contiguous image required')
    if visual[0]<0 or visual[-1]>=embeddings.shape[1] or not 1<=k<=len(visual):raise ValueError('Prior image bounds/budget')
    cache=DynamicCache(config=model.config) if use_cache else None
    hidden=embeddings;positions=position_ids;mask=torch.ones(embeddings.shape[:2],device=hidden.device,dtype=torch.long)
    def masks():
        options=dict(config=model.config,inputs_embeds=hidden,attention_mask=mask,past_key_values=None,position_ids=positions[0])
        return {'full_attention':create_causal_mask(**options),'linear_attention':create_recurrent_attention_mask(**options)}
    mapping=masks();rope=model.rotary_emb(hidden,positions[1:]);captured={};trajectory=[];selection=None
    for index,layer in enumerate(model.layers):
        trajectory.append(int(hidden.shape[1]));before=hidden
        mixer=getattr(layer,'linear_attn',None);original=None
        if method=='DART' and index==boundary-1:
            original=mixer.chunk_gated_delta_rule
            def observe(query,key,value,**options):
                captured['keys']=key.detach().reshape(key.shape[0],key.shape[1],-1)
                return original(query,key,value,**options)
            mixer.chunk_gated_delta_rule=observe
        try:
            hidden=layer(hidden,position_embeddings=rope,attention_mask=mapping[layer.block_type],
                         position_ids=positions[0],past_key_values=cache,use_cache=use_cache)
        finally:
            if original is not None:mixer.chunk_gated_delta_rule=original
        if index==boundary-1:
            if method=='S2PRUNE':
                erc=torch.linalg.vector_norm((hidden[:,visual]-before[:,visual]).float(),dim=-1)[0]
                captured['erc']=erc.detach()
            if fixed_selection is not None:
                indices=list(fixed_selection);selection={'indices':indices,'source':'fixed CPU identity/continuation fixture'}
            elif method=='DART':
                selection=dart_select(model.norm(hidden)[0],captured['keys'][0],visual,k)
            else:
                if image is None or grid is None:raise ValueError('S2Prune original image and grid required')
                selection=s2prune_select(erc.detach().cpu().numpy(),image,grid,k,coarse_grid,protected=protected)
            indices=selection['indices']
            if len(indices)!=k or indices!=sorted(set(indices)) or indices[0]<0 or indices[-1]>=len(visual):raise ValueError('Invalid prior selection')
            if not set(protected_visual_indices(protected,len(visual),k))<=set(indices):raise ValueError('Prior selection removed protected anchors')
            retain=torch.ones(embeddings.shape[1],dtype=torch.bool,device=hidden.device);retain[visual]=False
            retain[visual[torch.tensor(indices,device=hidden.device)]]=True;keep=retain.nonzero().flatten()
            hidden=hidden.index_select(1,keep);positions=positions.index_select(2,keep);mask=mask.index_select(1,keep)
            rope=model.rotary_emb(hidden,positions[1:]);mapping=masks()
    return {'hidden_states':model.norm(hidden),'cache':cache,'positions':positions,'attention_mask':mask,
            'keep':keep,'selection':selection,'trajectory':trajectory,'signals':captured,
            'prefix_state_policy':'retain_full_consumed_recurrent_history','method':method}


def gprune_select(features,k,seconds=30):
    """G-Prune official single-view rule on projected Qwen tokens, FP32.

    Original fixed threshold .5, temperature .03, five propagation steps and
    degree normalization. W @ A**5 is evaluated by five vector products;
    this changes arithmetic order, not the registered propagation rule.
    No semantic support/anchors are injected. Distinct tied scores use index.
    """
    import numpy as np
    import time
    began=time.monotonic();f=np.asarray(features,dtype=np.float32);n=len(f)
    if f.ndim!=2 or not np.isfinite(f).all() or not 1<=k<=n:raise ValueError('G-Prune shape/count')
    norms=np.linalg.norm(f,axis=1);unit=f/np.maximum(norms[:,None],np.float32(1e-12));a=np.empty((n,n),np.float32)
    for start in range(0,n,64):
        if time.monotonic()-began>seconds:raise TimeoutError('G-Prune CPU resource guard')
        block=unit[start:start+64]@unit.T;block[block<.5]=0;block/=.03;block[np.abs(block)<1e-6]=-5000
        block-=block.max(axis=1,keepdims=True);np.exp(block,out=block);block/=block.sum(axis=1,keepdims=True);a[start:start+64]=block
    degree=(a>0).sum(1);weight=norms
    for _ in range(5):weight=weight@a
    score=weight/degree
    indices=np.lexsort((np.arange(n),-score))[:k]
    if time.monotonic()-began>seconds:raise TimeoutError('G-Prune CPU resource guard')
    return {'indices':sorted(map(int,indices)),'scores':score.tolist(),'seconds':time.monotonic()-began,'target_k':k,'source':'jytmelon/G-Prune@762c63771212104958ddbc508d0c421e95adafc9','feature_stage':'projected_single_Qwen_image_grid'}


def pack_injected_batch(input_ids,attention_mask,position_ids,embeddings,image_features,image_token_id,selections):
    """Actual tensor gather used by the future adapter; CPU tests use tensors only."""
    import torch
    if input_ids.ndim!=2 or position_ids.shape!=(3,*input_ids.shape):raise ValueError('Native3-axis batch required')
    if len(selections)!=len(input_ids) or len(image_features)!=len(input_ids):raise ValueError('Batch arity')
    plans=[];vectors=[]
    for i,selected in enumerate(selections):
        plan=visual_gather_plan(input_ids[i].detach().cpu().numpy(),position_ids[:,i].detach().cpu().numpy(),
            attention_mask[i].detach().cpu().numpy(),image_token_id,selected)
        original=torch.tensor(plan['original_visual_positions'],device=embeddings.device);features=image_features[i]
        if features.shape!=(len(original),embeddings.shape[-1]):raise ValueError('Projected visual tensor shape')
        full=embeddings[i].clone();full[original]=features.to(full.dtype)
        keep=torch.tensor(plan['retained_input_indices'],device=embeddings.device)
        vectors.append(full[keep]);plans.append(plan)
    length=max(len(v) for v in vectors);bs=len(vectors);hidden=embeddings.shape[-1]
    packed=embeddings.new_zeros((bs,length,hidden));mask=input_ids.new_zeros((bs,length));pos=input_ids.new_zeros((4,bs,length))
    for i,(v,p) in enumerate(zip(vectors,plans)):
        start=length-len(v);packed[i,start:]=v;mask[i,start:]=1;pos[0,i,start:]=torch.arange(len(v),device=pos.device)
        pos[1:,i,start:]=torch.as_tensor(p['retained_position_ids'],device=pos.device)
    delta=input_ids.new_tensor([[p['next_text_position']-length] for p in plans])
    return {'inputs_embeds':packed,'attention_mask':mask,'position_ids':pos,'rope_deltas':delta,'plans':plans}


def injected_generate(model,batch,image_features,selections,options,prepared=None):
    """Shared pre-decoder adapter. No loader or service startup; caller owns authorization.

    Fresh native generate caches, explicit original3-axis positions and normal
    generation sampling. Real-weight equivalence remains a smoke requirement.
    """
    from types import MethodType
    import threading
    if batch['input_ids'].shape[0] not in {1,2}:raise ValueError('Only registered batch sizes1/2')
    if any(k in options for k in ('past_key_values','inputs_embeds','position_ids','attention_mask')):raise ValueError('Cache/input injection in options')
    if not 1<=options.get('max_new_tokens',8192)<=8192:raise ValueError('Output cap')
    lock=getattr(model,'_rq41_request_lock',None)
    if lock is None:lock=threading.Lock();model._rq41_request_lock=lock
    if not lock.acquire(blocking=False):raise RuntimeError('Concurrent mutable model state')
    original=model._prepare_position_ids_for_generation;old_delta=model.model.rope_deltas
    had_override='_prepare_position_ids_for_generation' in model.__dict__
    try:
        if prepared is None:
            positions,_=model.model.get_rope_index(batch['input_ids'],attention_mask=batch['attention_mask'],
                image_grid_thw=batch['image_grid_thw'],mm_token_type_ids=batch['mm_token_type_ids'])
            embeddings=model.get_input_embeddings()(batch['input_ids'])
            packed=pack_injected_batch(batch['input_ids'],batch['attention_mask'],positions,embeddings,image_features,model.config.image_token_id,selections)
        else:
            packed=prepared
            if len(packed['plans'])!=len(selections):raise ValueError('Prepared gather batch differs')
            if any(p['selected_visual_indices'].tolist()!=list(s) for p,s in zip(packed['plans'],selections)):
                raise ValueError('Prepared gather selection differs')
        if packed['inputs_embeds'].shape[1]+options.get('max_new_tokens',8192)>40960:raise ValueError('Context cap')
        model.model.rope_deltas=packed['rope_deltas']
        def prepare(this,inputs_tensor,kwargs):
            cache=kwargs.get('past_key_values')
            if cache is None or cache.get_seq_length()==0:return packed['position_ids']
            return original(inputs_tensor,kwargs)
        model._prepare_position_ids_for_generation=MethodType(prepare,model)
        return model.generate(inputs_embeds=packed['inputs_embeds'],attention_mask=packed['attention_mask'],
            position_ids=packed['position_ids'],use_cache=True,**options)
    finally:
        if had_override:model._prepare_position_ids_for_generation=original
        elif '_prepare_position_ids_for_generation' in model.__dict__:del model._prepare_position_ids_for_generation
        model.model.rope_deltas=old_delta;lock.release()


def rca_schema():
    return {'type':'object','properties':{'services':{'type':'array','minItems':5,'maxItems':5,'uniqueItems':True,'items':{'type':'string'}},
        'reason':{'type':'string'},'confidence':{'enum':['high','medium','low']}},'required':['services','reason','confidence'],'additionalProperties':False}


def rca_generation_schema(profile=None):
    """Static public syntax only; no case-specific candidates enter decoding."""
    schema=rca_schema()
    if profile is None:return schema
    if profile!='public_numeric_id_v23':raise ValueError('Unregistered RCA generation schema')
    schema['properties']['services']['items']['pattern']='^[1-9][0-9]{2,4}$'
    return schema


def local_rca_scorer():
    """Canonical metrics with the existing project-owned granularity matcher.

    Both the factory and default scorer use the central scorer package.
    No experiment-local matching rules, environment fallback or external checkout.
    """
    from scorer import RCAScorer,RCAScorerConfig,is_granularity_aware_hit
    return RCAScorer(RCAScorerConfig.load(),hit=is_granularity_aware_hit)


class SingleCallRunner:
    """Durable single-call transaction; injected provider allows offline qualification.

    Completion markers are trusted before input materialization. Independent
    repeats have separate keys/seeds; identical-input references are explicit.
    """
    def __init__(self,root,provider,limit,scope='rq41',offline=False):
        import fcntl
        from vlmrca.run_state import DurableCallRegister
        # Resolve scoring dependencies before acquiring a ledger or calling a provider.
        self.scorer=local_rca_scorer()
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=(self.root/'owner.lock').open('a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:self.lock.close();raise
        self.provider=provider;self.calls=DurableCallRegister(self.root/'calls.sqlite',limit=limit,scope=scope)
        self.offline=offline
    def close(self):self.lock.close()
    def flag(self,key):
        if Path(key).name!=key:raise ValueError('Unsafe call key')
        p=self.root/'completed'/(key+'.json')
        return read_json(p) if p.exists() else None
    def run(self,key,materialize,candidates,accepted=(),repeat=False,reference=None,fail_at=None,retry=False):
        from concurrent.futures import ThreadPoolExecutor
        from vlmrca.run_state import write_json
        from scorer import score_bound_response
        if self.flag(key):return self.flag(key)
        if (self.root/'PAUSE').exists():return {'status':'paused','committed':False}
        if not self.offline:raise PermissionError('GPU activation credential not installed')
        request=materialize();request_hash=stable_hash(request)
        if reference is not None:
            if repeat:raise ValueError('A repeat cannot reference a prior answer')
            origin=self.flag(reference)
            if not origin or origin['request_hash']!=request_hash:raise ValueError('Reference requires exact current request')
            result={**origin,'call_key':key,'reference':reference,'actual_calls':0};save_json(self.root/'completed'/(key+'.json'),result);return result
        cached=self.calls.cached(key,request_hash,'solver',retry=retry)
        if cached is None:
            attempt,_=self.calls.begin(key,request_hash,'solver',retry=retry)
            if fail_at=='before_provider':raise RuntimeError('Simulated process interruption')
            response=self.provider(request)
            result={'call_key':key,'request_hash':request_hash,'role':'solver','attempt_id':attempt,'response':response,'artifact_hashes':{},'actual_calls':1}
            path=self.root/'trajectories'/(key+f'__call{attempt}.json')
            with ThreadPoolExecutor(max_workers=1) as writer:
                writer.submit(write_json,path,result).result()
            if fail_at=='after_response':raise RuntimeError('Simulated reply-persistence interruption')
            result['artifact_hashes'][str(path.relative_to(self.root))]=digest(path)
            self.calls.finish(attempt,result);cached=result
        # Validation failures are committed outcomes, never answer-correctness retries.
        score=score_bound_response(cached['response'],candidates,{x:x for x in candidates},accepted,rca_schema(),self.scorer)
        result={**cached,'outcome':score,'repeat':repeat}
        if fail_at=='before_commit':raise RuntimeError('Simulated completion-marker interruption')
        save_json(self.root/'completed'/(key+'.json'),result);return result
    def recover(self):
        def audit(record,root):
            if not isinstance(record.get('response'),str) or not isinstance(record.get('artifact_hashes'),dict):raise ValueError('Bad persisted reply')
        return self.calls.recover_persisted(self.root,audit=audit)


class DeploymentJournal:
    """Production transaction: immutable replies, async commits and fast resume."""
    def __init__(self,root,limit,scope,scorer):
        import fcntl
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from vlmrca.run_state import DurableCallRegister
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.scorer=scorer
        self.lock=(self.root/'execution.lock').open('a')
        try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:self.lock.close();raise
        self.calls=DurableCallRegister(self.root/'calls.sqlite',limit=limit,scope=scope)
        self.writer=ThreadPoolExecutor(max_workers=1);self.futures=[];self.scope=scope;self.future_lock=threading.RLock()
    def completed(self,key):return (self.root/'completed'/(key+'.json')).exists()
    def begin(self,unit,request):
        key=unit['key']
        if Path(key).name!=key:raise ValueError('Unsafe deployment key')
        if self.completed(key):return None
        fingerprint=request['request_hash']
        existing=self.calls.cached(key,fingerprint,'solver',retry=True)
        if existing is not None:
            save_json(self.root/'completed'/(key+'.json'),existing);return None
        attempt,_=self.calls.begin(key,fingerprint,'solver',retry=True)
        save_json(self.root/'requests'/(key+'.json'),{'unit':unit,'request':request})
        return attempt
    def commit(self,unit,request,raw,attempt,fail_at=None):
        key=unit['key'];path=self.root/'trajectories'/(key+f'__call{attempt}.json')
        record={**raw,'call_key':key,'attempt_id':attempt,'request_hash':request['request_hash'],
            'role':'solver','unit':unit,'artifact_hashes':{},'actual_calls':1}
        save_json(path,record)
        if fail_at=='after_reply':raise RuntimeError('Injected interruption after durable raw reply')
        result={**record,'outcome':self.scorer(request,record['response'])}
        result['artifact_hashes'][str(path.relative_to(self.root))]=digest(path)
        result['artifact_hashes'][str((self.root/'requests'/(key+'.json')).relative_to(self.root))]=digest(self.root/'requests'/(key+'.json'))
        self.calls.finish(attempt,result)
        if fail_at=='after_ledger':raise RuntimeError('Injected interruption after ledger commit')
        save_json(self.root/'completed'/(key+'.json'),result)
        return result
    def submit(self,*args):
        with self.future_lock:
            self.check_writes();future=self.writer.submit(self.commit,*args);self.futures.append(future);return future
    def check_writes(self):
        with self.future_lock:
            pending=[]
            for future in self.futures:
                if future.done():future.result()
                else:pending.append(future)
            self.futures=pending
    def drain(self):
        with self.future_lock:
            for future in self.futures:future.result()
            self.futures=[]
    def recover(self):
        prefix=self.scope+'/'
        with self.calls.connect() as db:
            rows=db.execute('SELECT id,call_key,request_hash,state,result FROM calls WHERE substr(call_key,1,?)=? ORDER BY id',(len(prefix),prefix)).fetchall()
        recovered=[];interrupted=[]
        for attempt,full_key,fingerprint,state,result in rows:
            key=full_key[len(prefix):]
            if self.completed(key):continue
            if state=='complete':save_json(self.root/'completed'/(key+'.json'),json.loads(result));recovered.append(key);continue
            if state!='started':continue
            path=self.root/'trajectories'/(key+f'__call{attempt}.json')
            if path.exists():
                raw=read_json(path);item=read_json(self.root/'requests'/(key+'.json'))
                if raw['request_hash']!=fingerprint or raw['attempt_id']!=attempt:raise ValueError('Recovery reply identity mismatch')
                # Score the persisted raw answer, never generate it again.
                final={**raw,'outcome':self.scorer(item['request'],raw['response'])}
                final['artifact_hashes']={str(path.relative_to(self.root)):digest(path)}
                self.calls.finish(attempt,final);save_json(self.root/'completed'/(key+'.json'),final);recovered.append(key)
            else:
                self.calls.finish(attempt,{'reason':'owner_stopped_without_persisted_reply'},'interrupted');interrupted.append(key)
        return {'recovered':recovered,'interrupted_spent_attempts':interrupted}
    def disposition(self,unit,reason):
        self.drain();save_json(self.root/'completed'/(unit['key']+'.json'),{'status':'not_applicable','unit':unit,'reason':reason,'actual_calls':0})
    def finish_phase(self,backend,units):
        self.drain()
        if not all(self.completed(u['key']) for u in units):raise ValueError('Cannot complete an undrained/incomplete phase')
        save_json(self.root/('phase_complete.'+backend+'.json'),{'backend':backend,'positions':len(units),'keys_hash':stable_hash([u['key'] for u in units])})
    def close(self):
        try:self.drain()
        finally:self.writer.shutdown(wait=True);self.lock.close()


def attention_key_regions(manifest,grid,input_ids,image_token_id,selections=None):
    """Disjoint physical-key categories from actual DOM/processor geometry.

    Bounding-area categories are instrumentation locations, not proof of which
    fact a contextualized embedding carries. Ambiguous token cells stay mixed.
    """
    import numpy as np
    from collections import defaultdict
    height,width=grid;source=manifest['source_png'];sx=width/source['width'];sy=height/source['height']
    if 'header' not in manifest['audit']:raise ValueError('Actual header geometry missing for attention map')
    names=['text:instructions','image:title','image:relations','image:labels','image:observations','image:other','image:mixed']
    areas=defaultdict(lambda:defaultdict(float))
    rows=[('image:title',manifest['audit']['header'])]
    for b in manifest['audit']['bindings']:
        key=b['key'];name='image:title' if key.endswith('.title') else 'image:relations' if '.edge.' in key else 'image:labels' if any(x in key for x in ('.identity.','.node.','.entity','.unit','.time','.label','.operation')) else 'image:observations'
        rows.append((name,b))
    for name,b in rows:
        x0,x1=b['x']*sx,(b['x']+b['width'])*sx;y0,y1=b['y']*sy,(b['y']+b['height'])*sy
        for y in range(max(0,math.floor(y0)),min(height,math.ceil(y1))):
            for x in range(max(0,math.floor(x0)),min(width,math.ceil(x1))):
                areas[y*width+x][name]+=max(0,min(x+1,x1)-max(x,x0))*max(0,min(y+1,y1)-max(y,y0))
    tags=[]
    for i in range(width*height):
        support=areas[i]
        if not support:tags.append(names.index('image:other'))
        elif len(support)==1:tags.append(names.index(next(iter(support))))
        else:tags.append(names.index('image:mixed'))
    ids=np.asarray(input_ids);visual=np.flatnonzero(ids==image_token_id)
    if len(visual)!=len(tags):raise ValueError('Attention map grid differs from actual request')
    mapping=np.zeros(len(ids),np.int16);mapping[visual]=tags
    if selections is not None:
        keep=ids!=image_token_id;keep[visual[np.asarray(selections,dtype=int)]]=True;mapping=mapping[keep]
    return {'regions':names,'key_region':mapping,'map_hash':hashlib.sha256(mapping.tobytes()).hexdigest(),
        'kind':'exclusive_DOM_area_category_with_explicit_mixed_cells'}


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


class SmokeLogitsCapture:
    """Capture only registered finite pre-grammar logits; never another forward."""
    def __init__(self,progress_path=None,capture_logits=True):
        self.step=0;self.values={};self.first_cuda=None;self.first_wall=None
        self.progress_path=progress_path;self.initial_length=None;self.capture_logits=capture_logits
    def __call__(self, input_ids, scores):
        import torch
        if self.step==0:
            import time
            self.first_wall=time.monotonic()
            if scores.is_cuda:self.first_cuda=torch.cuda.Event(enable_timing=True);self.first_cuda.record()
            self.initial_length=input_ids.shape[1]
        if self.progress_path is not None and self.step%128==0:
            save_json(self.progress_path,{'generated_steps':self.step,'partial_only':True,
                'generated_token_ids':input_ids[:,self.initial_length:].detach().cpu().tolist()})
        if self.capture_logits and self.step in (0,1,2,4,8,16,32):
            if not torch.isfinite(scores).all():raise ValueError('Nonfinite unmasked model logits')
            self.values[self.step]=scores.detach().float().cpu()
        self.step+=1
        return scores


def __getattr__(name):
    """Load the production vLLM adapter only in the native serving process."""
    if name!='VLLMRankingPrefix':raise AttributeError(name)
    from vllm.v1.sample.logits_processor import AdapterLogitsProcessor
    class VLLMRankingPrefix(AdapterLogitsProcessor):
        def __init__(self,vllm_config,device,is_pin_memory):
            super().__init__(vllm_config,device,is_pin_memory)
            from transformers import AutoTokenizer
            self.tokenizer=AutoTokenizer.from_pretrained(vllm_config.model_config.tokenizer,local_files_only=True)
        def is_argmax_invariant(self):return True
        def new_req_logits_processor(self,params):
            import torch
            extra=params.extra_args or {}
            if extra.get('rq41_ranking_profile')!='ranking_prefix_greedy_v25':
                raise ValueError('Native RCA request lacks its registered decoder profile')
            done=False;steps=0
            def process(output_ids,scores):
                nonlocal done,steps
                if done:return scores
                if ranking_array_complete(self.tokenizer.decode(output_ids,skip_special_tokens=True)):
                    done=True
                    key=extra.get('rq41_audit_key');folder=os.environ.get('CANVASRCA_RQ41_NATIVE_DECODER_AUDIT')
                    if folder and key:
                        import re
                        if not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('Unsafe decoder audit key')
                        save_json(Path(folder)/(key+'.json'),{'profile':'ranking_prefix_greedy_v25','ranking_complete':True,
                            'forced_steps':steps,'release_generated_tokens':len(output_ids),'candidate_values_accessed':False})
                    return scores
                steps+=1;index=scores.argmax(-1,keepdim=True)
                return torch.full_like(scores,float('-inf')).scatter(0,index,scores.gather(0,index))
            return process
    VLLMRankingPrefix.__module__=__name__;VLLMRankingPrefix.__qualname__=name
    globals()[name]=VLLMRankingPrefix
    return VLLMRankingPrefix


def hybrid_prior_generate(model,batch,image_features,k,method,options,image=None,grid=None,fixed_selection=None,protected=None):
    """Native generation with one hybrid mid-layer prefill; no second model call."""
    import torch
    from types import MethodType
    from transformers.modeling_outputs import BaseModelOutputWithPast
    text=model.model.language_model;native=text.forward;prepare=model._prepare_position_ids_for_generation
    old_delta=model.model.rope_deltas;state={}
    had_forward='forward' in text.__dict__;had_prepare='_prepare_position_ids_for_generation' in model.__dict__
    positions,_=model.model.get_rope_index(batch['input_ids'],attention_mask=batch['attention_mask'],
        image_grid_thw=batch['image_grid_thw'],mm_token_type_ids=batch['mm_token_type_ids'])
    embeddings=model.get_input_embeddings()(batch['input_ids']);visual=(batch['input_ids'][0]==model.config.image_token_id).nonzero().flatten()
    embeddings[0,visual]=image_features[0].to(embeddings.dtype)
    n=embeddings.shape[1];four=torch.cat((torch.arange(n,device=embeddings.device).view(1,1,n),positions),dim=0)
    next_position=int(positions.max())+1
    def position_override(this,inputs_tensor,kwargs):
        cache=kwargs.get('past_key_values')
        if cache is None or cache.get_seq_length()==0:return four
        offset=cache.get_seq_length()-state['input_tokens']
        return torch.full((4,1,1),next_position+offset,device=embeddings.device,dtype=torch.long)
    def forward(this,input_ids=None,attention_mask=None,position_ids=None,past_key_values=None,inputs_embeds=None,use_cache=None,**kwargs):
        if not state:
            result=hybrid_prior_prefill(this,inputs_embeds,four,visual,k,method,image=image,grid=grid,fixed_selection=fixed_selection,protected=protected)
            state.update(input_tokens=int(result['hidden_states'].shape[1]),selection=result['selection'],
                trajectory=result['trajectory'],retained_position_ids=result['positions'].detach().cpu().tolist(),
                next_text_position=next_position,prefix_state_policy=result['prefix_state_policy'])
            model.model.rope_deltas=torch.tensor([[next_position-state['input_tokens']]],device=embeddings.device)
            return BaseModelOutputWithPast(last_hidden_state=result['hidden_states'],past_key_values=result['cache'])
        q=inputs_embeds.shape[1] if inputs_embeds is not None else input_ids.shape[1]
        length=past_key_values.get_seq_length()+q
        return native(input_ids=input_ids,attention_mask=torch.ones((1,length),device=embeddings.device,dtype=torch.long),
            position_ids=position_ids,past_key_values=past_key_values,inputs_embeds=inputs_embeds,use_cache=use_cache,**kwargs)
    text.forward=MethodType(forward,text);model._prepare_position_ids_for_generation=MethodType(position_override,model)
    try:
        result=model.generate(inputs_embeds=embeddings,attention_mask=batch['attention_mask'],position_ids=four,use_cache=True,**options)
        return result,state
    finally:
        if had_forward:text.forward=native
        else:del text.forward
        if had_prepare:model._prepare_position_ids_for_generation=prepare
        else:del model._prepare_position_ids_for_generation
        model.model.rope_deltas=old_delta
