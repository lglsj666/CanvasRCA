# AOT ID: ['0_inference']
from ctypes import c_void_p, c_long, c_int
import torch
import math
import random
import os
import tempfile
from math import inf, nan
from cmath import nanj
from torch._inductor.hooks import run_intermediate_hooks
from torch._inductor.utils import maybe_profile
from torch._inductor.codegen.memory_planning import _align as align
from torch import device, empty_strided
from torch._inductor.async_compile import AsyncCompile
from torch._inductor.select_algorithm import extern_kernels
import triton
import triton.language as tl
from torch._inductor.runtime.triton_heuristics import start_graph, end_graph
from torch._C import _cuda_getCurrentRawStream as get_raw_stream

aten = torch.ops.aten
inductor_ops = torch.ops.inductor
_quantized = torch.ops._quantized
assert_size_stride = torch._C._dynamo.guards.assert_size_stride
assert_alignment = torch._C._dynamo.guards.assert_alignment
empty_strided_cpu = torch._C._dynamo.guards._empty_strided_cpu
empty_strided_cpu_pinned = torch._C._dynamo.guards._empty_strided_cpu_pinned
empty_strided_cuda = torch._C._dynamo.guards._empty_strided_cuda
empty_strided_xpu = torch._C._dynamo.guards._empty_strided_xpu
empty_strided_mtia = torch._C._dynamo.guards._empty_strided_mtia
reinterpret_tensor = torch._C._dynamo.guards._reinterpret_tensor
alloc_from_pool = torch.ops.inductor._alloc_from_pool
async_compile = AsyncCompile()
empty_strided_p2p = torch._C._distributed_c10d._SymmetricMemory.empty_strided_p2p


# kernel path: /home/lglsj/CanvasRCA_nibi/build/cache/rq3/torchinductor/vw/cvwypsct42yzykp4qwgnouezmw3qr5tvkps567tom4wvn2vblp22.py
# Topologically Sorted Source Nodes: [ge_1, sum_1], Original ATen: [aten.ge, aten.sum]
# Source node to ATen node mapping:
#   ge_1 => ge_2
#   sum_1 => sum_1
# Graph fragment:
#   %arg1_1 : Tensor "f32[u1, 248320][248320, 1]cuda:0" = PlaceHolder[target=arg1_1]
#   %arg3_1 : Tensor "f32[u1, 1][1, 1]cuda:0" = PlaceHolder[target=arg3_1]
#   %ge_2 : Tensor "b8[u1, 248320][248320, 1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.ge.Tensor](args = (%arg1_1, %arg3_1), kwargs = {})
#   %sum_1 : Tensor "i64[u1][1]cuda:0"[num_users=1] = call_function[target=torch.ops.aten.sum.dim_IntList](args = (%ge_2, [-1]), kwargs = {})
#   return %sum_1
triton_red_fused_ge_sum_0 = async_compile.triton('triton_red_fused_ge_sum_0', '''
import triton
import triton.language as tl

from torch._inductor.runtime import triton_helpers, triton_heuristics
from torch._inductor.runtime.triton_helpers import libdevice, math as tl_math
from torch._inductor.runtime.hints import AutotuneHint, ReductionHint, TileHint, DeviceProperties
triton_helpers.set_driver_to_gpu()

@triton_heuristics.reduction(
    size_hints={'x': 8192, 'r0_': 262144},
    reduction_hint=ReductionHint.INNER,
    filename=__file__,
    triton_meta={'signature': {'in_ptr0': '*fp32', 'in_ptr1': '*fp32', 'out_ptr0': '*i64', 'xnumel': 'i64', 'r0_numel': 'i64', 'XBLOCK': 'constexpr', 'R0_BLOCK': 'constexpr'}, 'device': DeviceProperties(type='cuda', index=0, multi_processor_count=188, cc=120, major=12, regs_per_multiprocessor=65536, max_threads_per_multi_processor=1536, max_threads_per_block=1024, warp_size=32), 'constants': {}, 'native_matmul': False, 'enable_fp_fusion': True, 'launch_pdl': False, 'disable_ftz': False, 'configs': [{(0,): [['tt.divisibility', 16]], (1,): [['tt.divisibility', 16]], (2,): [['tt.divisibility', 16]], (4,): [['tt.divisibility', 16]]}]},
    inductor_meta={'grid_type': 'Grid1D', 'autotune_hints': set(), 'kernel_name': 'triton_red_fused_ge_sum_0', 'mutated_arg_names': [], 'optimize_mem': True, 'no_x_dim': False, 'atomic_add_found': False, 'num_load': 2, 'num_store': 1, 'num_reduction': 1, 'backend_hash': '0E9C14D2DCB14DC08B3936EF85F3E9F70CDD496F6AE3BEDCF3EAE2E95FA709DF', 'assert_indirect_indexing': True, 'autotune_local_cache': True, 'autotune_pointwise': True, 'autotune_remote_cache': None, 'force_disable_caches': False, 'dynamic_scale_rblock': True, 'max_autotune': False, 'max_autotune_pointwise': False, 'min_split_scan_rblock': 256, 'spill_threshold': 16, 'store_cubin': False, 'deterministic': False, 'force_filter_reduction_configs': False, 'mix_order_reduction_allow_multi_stages': False, 'are_deterministic_algorithms_enabled': False, 'tiling_scores': {'x': 163840, 'r0_': 8136949760}}
)
@triton.jit
def triton_red_fused_ge_sum_0(in_ptr0, in_ptr1, out_ptr0, xnumel, r0_numel, XBLOCK : tl.constexpr, R0_BLOCK : tl.constexpr):
    r0_numel = 248320
    rnumel = r0_numel
    RBLOCK: tl.constexpr = R0_BLOCK
    xoffset = tl.program_id(0).to(tl.int64) * XBLOCK
    xindex = xoffset + tl.arange(0, XBLOCK)[:, None].to(tl.int64)
    xmask = xindex < xnumel
    r0_base = tl.arange(0, R0_BLOCK)[None, :].to(tl.int64)
    rbase = r0_base
    x0 = xindex
    tmp1 = tl.load(in_ptr1 + (x0), xmask, eviction_policy='evict_last')
    _tmp5 = tl.full([XBLOCK, R0_BLOCK], 0, tl.int64)
    for r0_offset in tl.range(0, r0_numel, R0_BLOCK):
        r0_index = r0_offset + r0_base
        r0_mask = r0_index < r0_numel
        roffset = r0_offset
        rindex = r0_index
        r0_1 = r0_index
        tmp0 = tl.load(in_ptr0 + (r0_1 + 248320*x0), r0_mask & xmask, eviction_policy='evict_first', other=0.0)
        tmp2 = tmp0 >= tmp1
        tmp3 = tmp2.to(tl.int64)
        tmp4 = tl.broadcast_to(tmp3, [XBLOCK, R0_BLOCK])
        tmp6 = _tmp5 + tmp4
        _tmp5 = tl.where(r0_mask & xmask, tmp6, _tmp5)
    tmp5 = tl.sum(_tmp5, 1)[:, None]
    tl.store(out_ptr0 + (x0), tmp5, xmask)
''', device_str='cuda')


async_compile.wait(globals())
del async_compile

class Runner:
    def __init__(self, partitions):
        self.partitions = partitions

    def recursively_apply_fns(self, fns):
        new_callables = []
        for fn, c in zip(fns, self.partitions):
            new_callables.append(fn(c))
        self.partitions = new_callables

    def call(self, args):
        arg0_1, arg1_1, arg2_1, arg3_1 = args
        args.clear()
        u0 = arg0_1
        u1 = arg2_1
        assert_size_stride(arg1_1, (u1, 248320), (248320, 1))
        assert_size_stride(arg3_1, (u1, 1), (1, 1))
        if not (u0 >= 1):
            raise RuntimeError('u0 >= 1')
        buf0 = None
        if not (1 <= u0):
            raise RuntimeError('1 <= u0')
        buf1 = None
        if not (u1 >= 1):
            raise RuntimeError('u1 >= 1')
        buf2 = None
        if not (u0 == u1):
            raise RuntimeError('Eq(u0, u1)')
        buf3 = None
        with torch.cuda._DeviceGuard(0):
            torch.cuda.set_device(0)
            buf4 = empty_strided_cuda((u1, ), (1, ), torch.int64)
            # Topologically Sorted Source Nodes: [ge_1, sum_1], Original ATen: [aten.ge, aten.sum]
            stream0 = get_raw_stream(0)
            triton_red_fused_ge_sum_0.run(arg1_1, arg3_1, buf4, u1, 248320, stream=stream0)
            del arg1_1
            del arg3_1
        return (buf4, )

runner = Runner(partitions=[])
call = runner.call
recursively_apply_fns = runner.recursively_apply_fns


def get_args():
    from torch._dynamo.testing import rand_strided
    arg0_1 = 42
    arg1_1 = rand_strided((42, 248320), (248320, 1), device='cuda:0', dtype=torch.float32)
    arg2_1 = 42
    arg3_1 = rand_strided((42, 1), (1, 1), device='cuda:0', dtype=torch.float32)
    return [arg0_1, arg1_1, arg2_1, arg3_1]


def benchmark_compiled_module(args, times=10, repeat=10):
    from torch._inductor.utils import print_performance
    fn = lambda: call(list(args))
    return print_performance(fn, times=times, repeat=repeat)


if __name__ == "__main__":
    from torch._inductor.wrapper_benchmark import compiled_module_main
    args = get_args()
    compiled_module_main('None', lambda times, repeat: benchmark_compiled_module(args, times=times, repeat=repeat))
