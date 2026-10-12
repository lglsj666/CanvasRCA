"""Opt-in, frozen Qwen vision attention partition; defaults are untouched.

Groups index spatial-merge cells in ORIGINAL processor order, not raster order.
This is a scoped operator on one unbatched image, not token pruning. The model
still computes original absolute/rotary positions before these hooks execute.
"""
from collections import Counter
from contextlib import contextmanager
import torch


def processor_order_map(raster_groups, grid_thw, merge=2):
    t,h,w = map(int,grid_thw)
    if t!=1 or h%merge or w%merge or len(raster_groups)!=(h//merge)*(w//merge):
        raise ValueError('One complete merged-grid image is required')
    # Transformers rearranges [t,h//m,m,w//m,m] to [t,h//m,w//m,m,m].
    # The merge-cell order is raster order; each cell has m*m consecutive patches.
    return list(raster_groups)


def patch_permutation(groups, merge=2, device='cpu'):
    labels={};canonical=[labels.setdefault(int(g),len(labels)) for g in groups]
    count=Counter(canonical);k=len(count)
    if k not in (1,4) or len(set(count.values()))!=1:
        raise ValueError('Only one or four exactly equal complete groups are supported')
    cells=torch.tensor(sorted(range(len(groups)),key=lambda i:(canonical[i],i)),dtype=torch.long,device=device)
    patch=(cells[:,None]*(merge*merge)+torch.arange(merge*merge,device=device)).flatten()
    return patch,torch.argsort(patch),k


@contextmanager
def partition_vision(vision, groups, partition_blocks=23):
    """Restore the original model after success AND exceptions; no weights change."""
    if getattr(vision,'_canvas_partition_active',False):
        raise RuntimeError('Concurrent/nested partition sessions are not supported')
    if len(vision.blocks)!=27 or partition_blocks!=23 or vision.spatial_merge_size!=2:
        raise ValueError('Frozen 27-block / 2x2-merger architecture required')
    _,_,k=patch_permutation(groups)
    if k==1:
        yield vision
        return
    handles=[];state={};vision._canvas_partition_active=True
    def before(index):
        def hook(module,args,kwargs):
            hidden=args[0] if args else kwargs['hidden_states']
            if index==0:
                if hidden.shape[0]!=len(groups)*4 or len(kwargs['cu_seqlens'])!=2:
                    raise ValueError('Partition accepts exactly one complete processor image')
                perm,inv,_=patch_permutation(groups,device=hidden.device)
                state.update(perm=perm,inv=inv,positions=tuple(p.index_select(0,perm) for p in kwargs['position_embeddings']),
                             cu=torch.arange(5,dtype=kwargs['cu_seqlens'].dtype,device=hidden.device)*(hidden.shape[0]//4))
                hidden=hidden.index_select(0,perm)
            elif not state:
                raise RuntimeError('Partition layer called out of order')
            new=dict(kwargs,cu_seqlens=state['cu'],position_embeddings=state['positions'])
            if args: return (hidden,*args[1:]),new
            new['hidden_states']=hidden
            return args,new
        return hook
    def restore(module,args,kwargs,output):
        result=output.index_select(0,state['inv'])
        state.clear()
        return result
    try:
        for index,block in enumerate(vision.blocks[:partition_blocks]):
            handles.append(block.register_forward_pre_hook(before(index),with_kwargs=True))
        handles.append(vision.blocks[partition_blocks-1].register_forward_hook(restore,with_kwargs=True))
        yield vision
    finally:
        for handle in handles:handle.remove()
        state.clear();del vision._canvas_partition_active
