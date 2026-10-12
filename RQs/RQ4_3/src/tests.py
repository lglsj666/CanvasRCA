"""Small CPU regressions for prerequisites, explicitly not full arm qualification."""
from pathlib import Path
import tempfile
import unittest
from .utils import ROOT,RESULTS,read,save,DOMAuditor
from .exps import (rectangle_cells,source_closure,grouped_delta,soft_image_reference,VisualPrefillAdapter,
    co_membership_change,type7,midranks,selection_objectives,greedy_source_selection,reorder_visual_prefix,
    selection_packet_projection,source_units)


def recurrence_reference(q,k,v,g,beta):
    """Independent tiny FP32 recurrence, reserved for tests (no production loop)."""
    import torch
    q=q.float();k=k.float();v=v.float()
    q=q*torch.rsqrt((q*q).sum(-1,keepdim=True)+1e-6)/(q.shape[-1]**.5)
    k=k*torch.rsqrt((k*k).sum(-1,keepdim=True)+1e-6)
    state=torch.zeros(q.shape[0],q.shape[2],q.shape[3],v.shape[3]);out=[]
    for i in range(q.shape[1]):
        state=state*torch.exp(g[:,i])[...,None,None]
        prediction=torch.einsum('bhk,bhkv->bhv',k[:,i],state)
        error=(v[:,i]-prediction)*beta[:,i,...,None]
        state=state+torch.einsum('bhk,bhv->bhkv',k[:,i],error)
        out.append(torch.einsum('bhk,bhkv->bhv',q[:,i],state))
    return torch.stack(out,dim=1)


class FrozenVisualInputRegression(unittest.TestCase):
    def test_frozen_identity_and_processor_guard(self):
        from unittest.mock import patch
        from . import exps,utils
        from contextlib import ExitStack
        import copy
        with tempfile.TemporaryDirectory() as temp,ExitStack() as stack:
            root=Path(temp);(root/'dashboard.png').write_bytes(b'qualified image bytes')
            save(root/'manifest.json',{'status':'passed'})
            save(root/'queue.json',{'model_fingerprint':'model'})
            for module in (exps,utils):stack.enter_context(patch.object(module,'ROOT',root))
            stack.enter_context(patch.object(utils,'queue_path',return_value=root/'queue.json'))
            actual={'image_tokens':4,'retained_input_tokens':7,'grid_thw':[1,4,4]}
            audit=stack.enter_context(patch.object(exps,'processor_audit',return_value=actual))
            render=stack.enter_context(patch('renderer.main.render',side_effect=AssertionError('Must not redraw frozen input')))
            req={'image':'dashboard.png','manifest':'manifest.json','prompt':'task','retained':[0,1],
                'groups':{'groups':{'s':[0,1]}},'operation':'P_LOCAL_BI','order':False,
                'seed':42,'task':'RCA','processor':copy.deepcopy(actual)}
            item={'identity':utils.generation_identity(req,'model')}
            got=exps.materialize_frozen_visual(item,req,root/'out',None)
            self.assertEqual(got,dict(req,identity=item['identity']));render.assert_not_called()
            self.assertEqual(read(root/'out/request.json'),got)
            for field,value in [('prompt','changed'),('seed',43),('retained',[0,2]),
                                ('groups',{'groups':{'s':[0],'t':[1]}})]:
                bad=copy.deepcopy(req);bad[field]=value
                with self.subTest(field=field),self.assertRaisesRegex(ValueError,'modified'):
                    exps.materialize_frozen_visual(item,bad,root/'bad',None)
            (root/'dashboard.png').write_bytes(b'changed pixels')
            with self.assertRaisesRegex(ValueError,'modified'):
                exps.materialize_frozen_visual(item,req,root/'bad',None)
            (root/'dashboard.png').write_bytes(b'qualified image bytes')
            audit.return_value=dict(actual,grid_thw=[1,2,8])
            with self.assertRaisesRegex(ValueError,'processor mismatch'):
                exps.materialize_frozen_visual(item,req,root/'bad',None)
            self.assertFalse((root/'bad/request.json').exists())


def frozen_visual_repair_case(item):
    """Affected CPU path only; preserves frozen inputs and creates no model call."""
    import shutil,time
    from .main import prepare_formal
    from .utils import RQ,generation_identity,queue_path
    dest=RQ/'results/repair_xsrp_v18/population_ram'/item['key'];started=time.monotonic()
    try:
        meta=prepare_formal(item,str(dest),False);request=read(ROOT/meta['request_path'])
        original=read(ROOT/item['request'])
        if request!=dict(original,attention=False,identity=item['identity']):raise ValueError('Frozen request fields changed')
        if generation_identity(request,read(queue_path())['model_fingerprint'])!=item['identity']:
            raise ValueError('Actual generation identity changed')
        return {'key':item['key'],'arm':item['arm'],'dataset':item['dataset'],'status':'passed',
            'input_tokens':request['processor']['retained_input_tokens'],
            'core':meta['timing']['core'],'seconds':time.monotonic()-started,'new_model_calls':0}
    finally:
        if dest.exists():shutil.rmtree(dest)


class HostSchedulingRegression(unittest.TestCase):
    def test_physical_and_smt_isolation(self):
        from .utils import runtime_cpu_partition
        topology={i:(0,i//2) for i in range(32)}
        plan=runtime_cpu_partition(topology=topology)
        self.assertEqual(plan['preparation_cores'],list(range(0,16,2)))
        self.assertEqual(plan['gpu_host_cpus'],list(range(16,32)))
        self.assertFalse(set(plan['preparation_siblings'])&set(plan['gpu_host_cpus']))
        self.assertEqual(len({topology[c] for c in plan['preparation_cores']}),8)

    def test_restricted_affinity_cannot_share_worker_cores(self):
        from .utils import runtime_cpu_partition
        with self.assertRaises(RuntimeError):runtime_cpu_partition(topology={i:(0,i//2) for i in range(30)})
        plan=runtime_cpu_partition(topology={100+i:(i//8,i%8) for i in range(16)})
        self.assertEqual(len(plan['gpu_host_cpus']),8)

    def test_immediate_stop_cannot_kill_reused_pid(self):
        import os
        from unittest.mock import patch
        from .utils import stop_formal_now
        with tempfile.TemporaryDirectory() as d:
            save(Path(d)/'progress.json',{'pid':os.getpid(),'completed':314})
            with patch('os.killpg') as kill:
                with self.assertRaises(RuntimeError):stop_formal_now(d)
                kill.assert_not_called()
            self.assertEqual(read(Path(d)/'execution/PAUSE')['mode'],'immediate_stop')


class ReservedCacheRegression(unittest.TestCase):
    def test_native_values_masks_storage_and_reset(self):
        import torch
        from transformers.cache_utils import DynamicCache
        from .utils import reserved_dynamic_cache
        model=PrefillIntegration.tiny_model();config=model.config
        expected=DynamicCache(config=config);actual=reserved_dynamic_cache(config,40,'cpu',torch.float32)
        layer=actual.layers[3];pointer=layer.backing_keys.data_ptr()
        for count in (24,1,3,1):
            k=torch.randn(1,2,count,8);v=torch.randn_like(k)
            self.assertEqual(actual.get_mask_sizes(count,3),expected.get_mask_sizes(count,3))
            a=actual.update(k,v,3);b=expected.update(k,v,3)
            for x,y in zip(a,b):self.assertTrue(torch.equal(x,y))
            self.assertEqual(actual.get_seq_length(),expected.get_seq_length())
            self.assertEqual(layer.backing_keys.data_ptr(),pointer)
        with self.assertRaises(RuntimeError):actual.update(torch.zeros(1,2,12,8),torch.zeros(1,2,12,8),3)
        actual.reset();self.assertEqual(actual.get_seq_length(),0)
        new=actual.update(torch.ones(1,2,2,8),torch.ones(1,2,2,8)*7,3)
        self.assertEqual(new[0].shape[-2],2);self.assertTrue(torch.equal(new[1],torch.full_like(new[1],7)))
        self.assertFalse(actual.is_compileable)

    def test_all_operations_prefill_decode_and_second_case(self):
        import torch,copy
        from transformers.cache_utils import DynamicCache
        from .utils import reserved_dynamic_cache
        modes=('U','P_LOCAL_BI','P_SOFT_IMAGE','P_DUAL','C_LOCAL_FORWARD','C_SHAM_BI','C_GLOBAL_BI')
        for mode in modes:
            with self.subTest(mode=mode):
                a=PrefillIntegration.tiny_model();b=copy.deepcopy(a)
                reserved=reserved_dynamic_cache(b.config,40,'cpu',torch.float32)
                for offset in (0,33):
                    native=DynamicCache(config=a.config);reserved.reset()
                    groups=[list(range(3,11)),list(range(11,19))];images=list(range(3,19))
                    aa=VisualPrefillAdapter(a,groups,images,mode=mode) if mode!='U' else None
                    bb=VisualPrefillAdapter(b,groups,images,mode=mode) if mode!='U' else None
                    from contextlib import nullcontext
                    tokens=(torch.arange(24)[None,:]+offset)%128
                    with torch.no_grad(),aa.prefill() if aa else nullcontext():x=a(tokens,past_key_values=native,use_cache=True)
                    with torch.no_grad(),bb.prefill() if bb else nullcontext():y=b(tokens,past_key_values=reserved,use_cache=True)
                    torch.testing.assert_close(x.last_hidden_state,y.last_hidden_state,atol=1e-6,rtol=1e-6)
                    for token in (25,27,32):
                        with torch.no_grad():
                            x=a(torch.tensor([[token]]),past_key_values=native,use_cache=True)
                            y=b(torch.tensor([[token]]),past_key_values=reserved,use_cache=True)
                        torch.testing.assert_close(x.last_hidden_state,y.last_hidden_state,atol=1e-6,rtol=1e-6)
                    if aa:self.assertEqual(aa.branch_calls,bb.branch_calls);aa.close();bb.close()
                    for i,kind in enumerate(a.config.layer_types):
                        if kind=='linear_attention':
                            torch.testing.assert_close(native.layers[i].recurrent_states[0],reserved.layers[i].recurrent_states[0])

    def test_generation_cache_guard_and_fresh_case(self):
        from types import SimpleNamespace
        import torch
        from transformers import GenerationConfig
        from transformers.generation.configuration_utils import GenerationMode
        from .utils import install_reserved_cache
        config_model=PrefillIntegration.tiny_model().config
        model=SimpleNamespace(config=SimpleNamespace(get_text_config=lambda:config_model))
        cache=install_reserved_cache(model,40,'cpu',torch.float32);config=GenerationConfig(do_sample=True,num_beams=1,num_return_sequences=1,use_cache=True)
        for _ in range(2):
            kw={};model._prepare_cache_for_generation(config,kw,GenerationMode.SAMPLE,1,39)
            self.assertIs(kw['past_key_values'],cache);self.assertEqual(cache.get_seq_length(),0)
            cache.update(torch.ones(1,2,8,8),torch.ones(1,2,8,8),3)
        with self.assertRaises(RuntimeError):model._prepare_cache_for_generation(config,{},GenerationMode.SAMPLE,1,41)
        with self.assertRaises(RuntimeError):model._prepare_cache_for_generation(config,{},GenerationMode.SAMPLE,2,20)

    def test_capacity_slots_return_and_long_wait(self):
        import threading,time
        from .utils import CapacitySlots
        slots=CapacitySlots([40,16,16]);a=slots.acquire(12);b=slots.acquire(12);c=slots.acquire(30)
        self.assertEqual((a,b,c),(1,2,0));done=[]
        thread=threading.Thread(target=lambda:done.append(slots.acquire(30)));thread.start()
        slots.release(a);self.assertFalse(done);slots.release(c);thread.join(timeout=1)
        self.assertEqual(done,[0]);slots.release(0);slots.release(b)
        with self.assertRaises(ValueError):slots.acquire(41)
        with self.assertRaises(RuntimeError):slots.release(0)


class Prerequisites(unittest.TestCase):
    def test_rectangle_union_and_edges(self):
        r={'x':16,'y':16,'width':32,'height':32}
        self.assertEqual(rectangle_cells(r,[64,64],[64,64]),{0,1,2,3})
        self.assertEqual(rectangle_cells({'x':0,'y':0,'width':32,'height':32},[64,64],[64,64]),{0})
        with self.assertRaises(ValueError):rectangle_cells(r,[64,64],[63,64])

    def test_closure_indivisible_and_choice(self):
        packet={'records':[{'source':f'a{i}','kind':'assignment','value':{'field':'trace_summary_entry'}} for i in range(3)],'candidates':['123']}
        evidence={'cards':[{'id':f'T{i}','kind':'trace','entity':'123'} for i in range(3)]}
        mapping=[{'source':f'a{i}','path':'/count','binding':f'T{i}.value','disposition':'visible','value_hash':str(i)} for i in range(3)]
        rectangles=[{'card':f'T{i}','x':i*64,'y':0,'width':64,'height':64} for i in range(3)]
        proc={'source_pixels':[192,64],'processed_pixels':[192,64]}
        result=source_closure(packet,mapping,evidence,rectangles,proc)
        self.assertEqual(result['closure_count'],3);self.assertTrue(result['selection_freedom_upper_bound'])
        mapping.append(dict(mapping[0],source='a1'));mapping.append(dict(mapping[2],source='a1'))
        result=source_closure(packet,mapping,evidence,rectangles,proc)
        self.assertEqual(result['closure_count'],1);self.assertFalse(result['selection_freedom_upper_bound'])
        mapping.append(dict(mapping[0],source='unknown'))
        with self.assertRaises(ValueError):source_closure(packet,mapping,evidence,rectangles,proc)

    def test_native_gdn_groups_padding_reverse(self):
        import torch
        torch.set_num_threads(1);torch.manual_seed(431)
        q,k,v=[torch.randn(1,85,2,4) for _ in range(3)]
        g=-torch.rand(1,85,2)*.2;beta=torch.rand(1,85,2)
        groups=[list(range(0,9)),list(range(10,77))]
        expected=torch.zeros_like(v)
        for group in groups:
            for positions in (group,list(reversed(group))):
                ref=recurrence_reference(q[:,positions],k[:,positions],v[:,positions],g[:,positions],beta[:,positions])
                expected[:,positions]+=ref/2
        result=grouped_delta(q,k,v,g,beta,groups)
        torch.testing.assert_close(result,expected,atol=2e-5,rtol=2e-5)
        torch.testing.assert_close(result,grouped_delta(q,k,v,g,beta,list(reversed(groups))),atol=0,rtol=0)
        forward=grouped_delta(q,k,v,g,beta,groups,False)
        for group in groups:
            torch.testing.assert_close(forward[:,group],recurrence_reference(q[:,group],k[:,group],v[:,group],g[:,group],beta[:,group]),atol=2e-5,rtol=2e-5)
        with self.assertRaises(ValueError):grouped_delta(q,k,v,g,beta,[[0,1],[1,2]])
        self.assertTrue(torch.equal(result[:,[9,77,84]],torch.zeros_like(result[:,[9,77,84]])))

    def test_soft_image_causality_and_zero_weight(self):
        import torch
        torch.manual_seed(432)
        q,k,v=[torch.randn(1,2,10,4) for _ in range(3)]
        image=[2,3,4,5];base=soft_image_reference(q,k,v,image,2,0)
        native=torch.nn.functional.scaled_dot_product_attention(q,k,v,is_causal=True)
        torch.testing.assert_close(base,native,atol=1e-6,rtol=1e-5)
        actual=soft_image_reference(q,k,v,image,2)
        changed_k=k.clone();changed_v=v.clone();changed_k[...,6:,:]+=100;changed_v[...,6:,:]+=100
        changed=soft_image_reference(q,changed_k,changed_v,image,2)
        torch.testing.assert_close(changed[...,:6,:],actual[...,:6,:],atol=0,rtol=0)
        text=[0,1,6,7,8,9]
        torch.testing.assert_close(actual[...,text,:],base[...,text,:],atol=0,rtol=0)
        self.assertGreater(float((actual[...,image,:]-base[...,image,:]).abs().max()),.001)

    def test_atomic_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'completed.json';save(path,{'value':1})
            try:save(path,{'value':float('nan')})
            except ValueError:pass
            self.assertEqual(read(path),{'value':1})
            save(path,{'value':2});self.assertEqual(read(path),{'value':2})

    def test_renderer_width_lower_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            directory=Path(directory);html=directory/'fixture.html'
            html.write_text('<html><body><section data-card="C" style="width:120px"><span class="title" '
                'data-binding="C.title" style="font:12px monospace;white-space:nowrap">ABCDEFGHIJKLMNO</span></section></body></html>')
            auditor=DOMAuditor(directory/'browser.log')
            try:
                job={'id':'fixture','html':str(html),'source_pixels':[256,256],'processed_pixels':[256,256],'min_font':18}
                failure=auditor.measure(job)
                self.assertEqual(failure['status'],'proven_infeasible')
                self.assertFalse(failure['qualification_pass'])
                html.write_text(html.read_text().replace('ABCDEFGHIJKLMNO','ABC'))
                good=auditor.measure(job)
                self.assertEqual(good['status'],'not_disproven');self.assertFalse(good['qualification_pass'])
            finally:auditor.close()


class PrefillIntegration(unittest.TestCase):
    @staticmethod
    def tiny_model():
        import torch
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5TextConfig
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5TextModel
        torch.set_num_threads(1);torch.manual_seed(4301)
        config=Qwen3_5TextConfig(vocab_size=128,hidden_size=32,intermediate_size=48,
            num_hidden_layers=4,num_attention_heads=4,num_key_value_heads=2,head_dim=8,
            linear_num_key_heads=2,linear_num_value_heads=4,linear_key_head_dim=4,linear_value_head_dim=4,
            linear_conv_kernel_dim=4,layer_types=['linear_attention']*3+['full_attention'],
            rope_parameters={'rope_type':'default','rope_theta':10000.,'partial_rotary_factor':1.,'mrope_section':[1,1,2]})
        config._attn_implementation='sdpa'
        return Qwen3_5TextModel(config).eval()

    def test_lambda_zero_exact_and_hook_cleanup(self):
        import torch
        model=self.tiny_model();tokens=torch.arange(24)[None,:]
        with torch.no_grad():original=model(tokens,use_cache=False).last_hidden_state
        adapter=VisualPrefillAdapter(model,[list(range(3,11)),list(range(11,19))],list(range(3,19)),mode='P_DUAL',weight=0)
        with torch.no_grad(),adapter.prefill():actual=model(tokens,use_cache=False).last_hidden_state
        self.assertTrue(torch.equal(original,actual));self.assertEqual(adapter.branch_calls,0)
        adapter.close()
        with torch.no_grad():restored=model(tokens,use_cache=False).last_hidden_state
        self.assertTrue(torch.equal(original,restored))

    def test_independent_prefill_and_decode_cache(self):
        import torch,copy
        original=self.tiny_model();reference=copy.deepcopy(original);tokens=torch.arange(24)[None,:]
        groups=[list(range(3,11)),list(range(11,19))];images=list(range(3,19))
        active=VisualPrefillAdapter(original,groups,images)
        independent=VisualPrefillAdapter(reference,groups,images,reference_kernel=recurrence_reference)
        with torch.no_grad(),active.prefill():a=original(tokens,use_cache=True)
        with torch.no_grad(),independent.prefill():b=reference(tokens,use_cache=True)
        torch.testing.assert_close(a.last_hidden_state,b.last_hidden_state,atol=2e-5,rtol=2e-5)
        self.assertEqual(active.branch_calls,3);self.assertEqual(independent.branch_calls,3)
        cache_chunk=copy.deepcopy(a.past_key_values)
        steps=[]
        for token in (24,25,26):
            with torch.no_grad():
                a=original(torch.tensor([[token]]),past_key_values=a.past_key_values,use_cache=True)
                b=reference(torch.tensor([[token]]),past_key_values=b.past_key_values,use_cache=True)
            torch.testing.assert_close(a.last_hidden_state,b.last_hidden_state,atol=2e-5,rtol=2e-5)
            steps.append(a.last_hidden_state)
        with torch.no_grad():chunk=original(torch.tensor([[24,25,26]]),past_key_values=cache_chunk,use_cache=True)
        torch.testing.assert_close(torch.cat(steps,dim=1),chunk.last_hidden_state,atol=2e-5,rtol=2e-5)
        self.assertEqual(active.branch_calls,3);active.close();independent.close()

    def test_soft_interface_gate_once_and_text_boundaries(self):
        import torch
        model=self.tiny_model();layer=model.layers[3].self_attn
        from transformers.models.qwen3_5 import modeling_qwen3_5 as native
        x=torch.randn(1,24,32);cos=torch.ones(1,24,8);sin=torch.zeros_like(cos)
        images=list(range(3,19));mask=torch.full((1,1,24,24),float('-inf')).triu(1)
        def expected():
            q,gate=torch.chunk(layer.q_proj(x).view(1,24,4,16),2,-1)
            q=layer.q_norm(q).transpose(1,2)
            k=layer.k_norm(layer.k_proj(x).view(1,24,2,8)).transpose(1,2)
            v=layer.v_proj(x).view(1,24,2,8).transpose(1,2)
            q,k=native.apply_rotary_pos_emb(q,k,cos,sin)
            k=native.repeat_kv(k,2);v=native.repeat_kv(v,2)
            value=soft_image_reference(q,k,v,images,3).transpose(1,2).reshape(1,24,32)
            return layer.o_proj(value*torch.sigmoid(gate.reshape(1,24,32)))
        with torch.no_grad():truth=expected()
        adapter=VisualPrefillAdapter(model,[],images,mode='P_SOFT_IMAGE')
        with torch.no_grad(),adapter.prefill():actual=layer(x,position_embeddings=(cos,sin),attention_mask=mask)[0]
        torch.testing.assert_close(actual,truth,atol=2e-6,rtol=2e-5)
        with torch.no_grad():
            changed=x.clone();changed[:,19:]+=100
            with adapter.prefill():changed_out=layer(changed,position_embeddings=(cos,sin),attention_mask=mask)[0]
        torch.testing.assert_close(changed_out[:,:19],actual[:,:19],atol=0,rtol=0)
        adapter.close()

    def test_sham_pair_count_formula(self):
        import itertools
        a=[[0,1,2],[3,4,5]];b=[[0,2,4],[1,3,5]]
        pairs=lambda gs:set(pair for g in gs for pair in itertools.combinations(g,2))
        expected=len(pairs(a)^pairs(b))/len(pairs(a)|pairs(b))
        self.assertEqual(co_membership_change(a,b),expected)
        self.assertEqual(co_membership_change(a,list(reversed(a))),0)

    def test_order_keeps_text_and_spatial_identity(self):
        import torch
        x=torch.arange(32.).reshape(1,16,2);coords=torch.arange(64).reshape(4,1,16)
        packet={'retained':[4,8,12,16],'order_token_source_by_slot':[[4,12],[8,16],[12,4],[16,8]]}
        delta=torch.tensor([123])
        out,pos,newdelta=reorder_visual_prefix(x,coords,packet,3,delta)
        torch.testing.assert_close(out[:,3:7],x[:,[5,6,3,4]],rtol=0,atol=0)
        torch.testing.assert_close(pos[0],coords[0],rtol=0,atol=0)
        torch.testing.assert_close(pos[-3:,:,3:7],coords[-3:,:,[5,6,3,4]],rtol=0,atol=0)
        self.assertIs(newdelta,delta)
        unchanged=list(range(3))+list(range(7,16));self.assertTrue(torch.equal(out[:,unchanged],x[:,unchanged]))


class SelectionRegression(unittest.TestCase):
    def test_anchor_pack_is_bounded_deterministic_and_keeps_shared_pixels(self):
        import numpy as np
        from .exps import pack_anchor_pixels
        from renderer.operations.anchor_pack import apply
        a=np.zeros((64,96),np.uint8);a[10:20,30:33]=255;a[40:44,50:60]=255
        dom={'blocks':[{'id':'A0','card':'c','box':[30,10,3,10],'panel':[0,0,96,64],'obstacles':[]},
            {'id':'A1','card':'c','box':[50,40,10,4],'panel':[0,0,96,64],'obstacles':[]}]}
        x=pack_anchor_pixels(a,dom);y=pack_anchor_pixels(a,dom)
        self.assertEqual(x,y);self.assertLessEqual(x['predicted_after'],x['before'])
        for b in x['offsets']:self.assertLessEqual(max(abs(b['dx']),abs(b['dy'])),16)
        design={};apply(design,x['offsets']);self.assertEqual(design['anchor_pack']['schema'],'AnchorPackV1')

    def test_uniform_without_features_matches_original_selector(self):
        import numpy as np
        from .exps import uniform_support_indices
        from RQs.RQ4_1.src.utils import select_tokens
        for height,width in ((3,4),(4,9)):
            n=height*width;xy=np.array([[i%width,i//width] for i in range(n)],np.float32)
            anchors=[0,n-1];optional=list(range(1,n-1))
            roles={'r':{'tokens':optional,'bbox_diag2':float(n*n),'patch_diag2':2.,'fully_anchored':False}}
            support={'grid':[height,width],'image_tokens':n,'anchors':anchors,'roles':roles}
            actual=uniform_support_indices(support)
            reference=select_tokens(np.ones((n,2),np.float32),xy,roles,anchors,[{'type':'fixture','roles':['r']}],
                mode='UNIFORM',budget_policy='optional_support_v3')
            self.assertEqual(actual['indices'],reference['indices'])
            with self.assertRaises(ValueError):uniform_support_indices(support,1)

    def test_reflow_preserves_values_and_selected_spacers(self):
        from .exps import selected_dashboard,reflow_layouts
        from .utils import roster
        from renderer.utils import compile_design
        row=roster()[0];base=ROOT/row['base'];original=read(base/'evidence.json')
        keep={c['id'] for c in original['cards']}
        e,d,p=selected_dashboard(base,keep)
        self.assertEqual(e,original)
        self.assertEqual(compile_design(e,d)['rectangles'],read(base/'render/geometry.json')['rectangles'])
        with self.assertRaises(ValueError):selected_dashboard(base,{'unknown'})

    def test_selected_prompt_scope_and_fail_closed(self):
        from .exps import selected_prompt
        text='Diagnose using the complete telemetry dashboard. All incident observations and the exhaustive candidate IDs are in the image. Return five IDs.'
        result=selected_prompt(text)
        self.assertIn('available telemetry dashboard',result)
        self.assertIn('The displayed observations',result)
        self.assertTrue(result.endswith('Return five IDs.'))
        self.assertIn('exhaustive candidate IDs',result)
        for wrong in ('unknown interface',text+text,result):
            with self.assertRaises(ValueError):selected_prompt(wrong)

    def test_explicit_pair_rows_and_shared_source_support(self):
        packet={'schema':'FullVisualSourceLedgerV1','candidates':['123','456','789'],
            'records':[{'source':s,'kind':kind,'value':{'rows':[['PAIR01',[1,2]],['PAIR02',[1,2]]]}}
                       for s,kind in [('a1','pair_binary'),('a2','pair_continuous')]]}
        public={'payload':{'relations':[{'id':'PAIR01','parent':'123','child':'456'},
            {'id':'PAIR02','parent':'123','child':'789'}]}}
        mapping=[{'source':s,'path':'/'+pair+'/value','binding':card+'.value','disposition':'visible','value_hash':'0'}
            for s in ['a1','a2'] for pair,card in [('PAIR01','C1'),('PAIR02','C2')]]
        expanded,bindings=selection_packet_projection(packet,mapping,public)
        self.assertEqual(len(expanded['records']),4)
        self.assertEqual({r['source'] for r in expanded['records']},{'a1/PAIR01','a1/PAIR02','a2/PAIR01','a2/PAIR02'})
        canonical,cards,excluded=source_units(packet,mapping,{'cards':[]})
        self.assertEqual(cards['C1'],{'request_pair:PAIR01'});self.assertEqual(cards['C2'],{'request_pair:PAIR02'})
        self.assertNotEqual(cards['C1'],cards['C2'])  # Equal values are NOT same source.

    def test_quantiles_and_ties(self):
        import numpy as np
        for data in ([0],[0,0,10],[1,9,3,-10,2],[-1e12,0,1e12]):
            for q in (.1,.5,.9):self.assertAlmostEqual(type7(data,q),float(np.quantile(data,q,method='linear')))
        self.assertEqual(midranks([1,1,3]),[.25,.25,1.]);self.assertEqual(midranks([10]),[.5])
        self.assertIsNone(type7([None],.5))
        with self.assertRaises(ValueError):type7([False],.5)

    def test_selector_pair_closure_cost_and_determinism(self):
        def descriptor(i,value):return {'id':str(i),'source':str(i),'closure':str(i),'owners':[str(i)],
            'entity_key':(str(i),),'modality':'M','key':('metric','unit'),'values':[value],'changes':[value]}
        descriptors=[descriptor(0,0),descriptor(1,1),descriptor(2,2)]
        sim,dist,weights=selection_objectives(descriptors)
        self.assertAlmostEqual(float(weights.sum()),1.)
        self.assertAlmostEqual(float(dist.sum()),2/3)
        self.assertAlmostEqual(float(sim[0,2]),0.)
        closure={'closures':[{'id':str(i),'protected':i==0} for i in range(3)]}
        domains={'0':{0,1},'1':{2,3},'2':{3,4}}
        for method in ['S_DISTINGUISH','S_REPRESENT','S_JOINT','C_SOURCE_HASH']:
            a=greedy_source_selection(closure,descriptors,domains,'fixture',method)
            b=greedy_source_selection(closure,list(reversed(descriptors)),domains,'fixture',method)
            self.assertEqual(a['selected'],b['selected']);self.assertIn('0',a['selected'])
            self.assertLessEqual(a['used_optional_cells'],a['optional_budget'])
        domains={'0':{0,1},'1':{2},'2':{3}}
        selected=greedy_source_selection(closure,descriptors,domains,'fixture','S_DISTINGUISH')
        self.assertEqual(selected['selected'],['0','2'])


class RuntimeRegression(unittest.TestCase):
    def test_repaired_failure_needs_versioned_receipt(self):
        from unittest.mock import patch
        from .utils import RuntimeSession
        with tempfile.TemporaryDirectory() as tmp,patch('RQs.RQ4_3.src.gates.execution_fingerprint',return_value='fixed-version'):
            session=RuntimeSession(tmp,limit=10);item={'key':'failed','identity':'a'*64,'task':'RCA'}
            aid,_=session.calls.begin(item['key'],item['identity'],item['task'])
            session.calls.finish(aid,{'error':'transport'},'infrastructure_failure')
            def reached(*args):raise LookupError('materialization reached')
            with self.assertRaises(RuntimeError):session.run(item,reached,None,None)
            save(Path(tmp)/'infrastructure_repairs.json',{'execution_fingerprint':'wrong','attempt_ids':[aid]})
            with self.assertRaises(RuntimeError):session.run(item,reached,None,None)
            save(Path(tmp)/'infrastructure_repairs.json',{'execution_fingerprint':'fixed-version','attempt_ids':[aid]})
            with self.assertRaises(LookupError):session.run(item,reached,None,None)
            self.assertEqual(session.calls.summary(),{'infrastructure_failure':1});session.close()

    def test_atomic_resume_and_independent_calls(self):
        from .utils import RuntimeSession
        import json
        class Provider:
            calls=0;last_usage={'input_tokens':2,'output_tokens':3}
            def __call__(self,request):
                self.calls+=1
                return json.dumps({'services':['101','102','103','104','105'],'reason':'x','confidence':'low'})
        context=lambda item:{'candidates':['101','102','103','104','105'],
            'numeric_to_natural':{str(100+i):str(i) for i in range(1,6)},'accepted':['1']}
        request={'identity':'a'*64,'prompt':'static','image':None,'retained':[],'groups':{},'operation':'TEXT',
            'order':False,'seed':1,'task':'RCA','attention':False,'manifest':None,'processor':{}}
        item={'key':'case__arm','identity':'a'*64,'task':'RCA'}
        validate=lambda *args:{'status':'passed'}
        for point in ('before_provider','after_response','after_ledger','before_commit','after_commit'):
            with self.subTest(point=point),tempfile.TemporaryDirectory() as tmp:
                provider=Provider();session=RuntimeSession(tmp,provider,limit=10)
                def fail(stage):
                    if stage==point:raise RuntimeError('simulated power loss')
                with self.assertRaises(RuntimeError):session.run(item,lambda *args:request,context,validate,fail)
                session.close();session=RuntimeSession(tmp,provider,limit=10);session.recover()
                result=session.run(item,lambda *args:request,context,validate)
                self.assertEqual(provider.calls,1);self.assertEqual(result['outcome']['metrics']['mrr'],1)
                def forbidden(*args):raise AssertionError('Committed input reopened')
                session.run(item,forbidden,forbidden,forbidden)
                alias={**item,'key':'alias','reference':item['key']};session.run(alias,forbidden,forbidden,forbidden)
                self.assertEqual(provider.calls,1)
                repeat={**item,'key':'independent'};session.run(repeat,lambda *args:request,context,validate)
                self.assertEqual(provider.calls,2)
                with self.assertRaises(BlockingIOError):RuntimeSession(tmp,provider,limit=10)
                save(Path(tmp)/'PAUSE',{});self.assertEqual(session.run({**item,'key':'pending'},forbidden,forbidden,forbidden)['status'],'paused')
                session.close()

    def test_qa_denominator_and_numeric_truth(self):
        import json
        from .utils import score_factual
        questions={q:{'applicable':False} for q in ('q1','q2','q3','q4','q5','q6')}
        questions['q1']={'applicable':True,'kind':'numeric','answer':'1.20','integer_count':False,'unit':'ms'}
        questions['q4']={'applicable':True,'kind':'numeric','answer':'120','integer_count':True,'unit':'count'}
        answer={q:'unavailable' for q in questions};answer.update(q1='1.204 ms',q4='120')
        visibility={'q1':True,'q4':False};packet={'questions':questions}
        r=score_factual(json.dumps(answer),packet,visibility);self.assertEqual(r['score'],.5);self.assertEqual(r['coverage'],.5)
        answer['q1']='1.206';self.assertEqual(score_factual(json.dumps(answer),packet,visibility)['score'],0)
        answer['q1']='NaN';self.assertEqual(score_factual(json.dumps(answer),packet,visibility)['score'],0)
        answer['q1']='1.20 s';self.assertEqual(score_factual(json.dumps(answer),packet,visibility)['score'],0)
        visibility['q4']=True;answer['q4']='120.1';self.assertEqual(score_factual(json.dumps(answer),packet,visibility)['score'],0)

    def test_no_model_allocation_without_credential(self):
        from .gates import require_execution
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp,patch('RQs.RQ4_3.src.utils.execution_folder',return_value=Path(tmp)):
            with self.assertRaises((FileNotFoundError,RuntimeError)):require_execution('formal')

    def test_qa_display_phase_case_without_unit_conversion(self):
        from .utils import score_factual
        import json
        q={name:{'applicable':False} for name in ('q1','q2','q3','q4','q5','q6')}
        q['q5']={'applicable':True,'kind':'binding','answer':{'entity_id':'125','unit':'µs','phase':'current'}}
        answer={name:'unavailable' for name in q};answer['q5']={'entity_id':'125','unit':'us','phase':'Current'}
        self.assertEqual(score_factual(json.dumps(answer),{'questions':q},{'q5':True})['score'],1)
        answer['q5']['phase']='Reference';self.assertEqual(score_factual(json.dumps(answer),{'questions':q},{'q5':True})['score'],0)
        answer['q5']['phase']='Current';answer['q5']['unit']='ms'
        self.assertEqual(score_factual(json.dumps(answer),{'questions':q},{'q5':True})['score'],0)



class XSRPRegression(unittest.TestCase):
    def test_append_gate_needs_versioned_cpu_and_explicit_waiver(self):
        from unittest.mock import patch
        from .gates import require_execution
        from .utils import digest
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'deployment_v8';folder.mkdir()
            save(folder/'queue.json',{'positions':2632})
            save(folder/'cpu_qualification.json',{'status':'passed','execution_fingerprint':'f','queue_sha256':digest(folder/'queue.json'),'positions':2632})
            save(folder/'activation.json',{'formal':True,'execution_fingerprint':'f'})
            with patch('RQs.RQ4_3.src.utils.execution_folder',return_value=folder),patch('RQs.RQ4_3.src.gates.execution_fingerprint',return_value='f'):
                with self.assertRaises(FileNotFoundError):require_execution('formal')
                save(folder/'gpu_waiver.json',{'status':'user_waived_after_complete_cpu','execution_fingerprint':'old'})
                with self.assertRaises(RuntimeError):require_execution('formal')
                save(folder/'gpu_waiver.json',{'status':'user_waived_after_complete_cpu','execution_fingerprint':'f'})
                require_execution('formal')
                save(folder/'queue.json',{'positions':2631})
                with self.assertRaises(RuntimeError):require_execution('formal')

    def test_generation_alias_is_not_new_computation(self):
        from .utils import generation_identity
        r={'prompt':'static','image':None,'seed':9,'operation':'P_LOCAL_BI','groups':{'groups':{'x':[1,4],'y':[2,3]}},
           'retained':[1,2,3,4],'order':False,'task':'RCA'}
        s={**r,'groups':{'groups':{'renamed':[3,2],'other':[4,1]}}}
        self.assertEqual(generation_identity(r,'m'),generation_identity(s,'m'))
        s['groups']['groups']['renamed']=[1,2]
        self.assertNotEqual(generation_identity(r,'m'),generation_identity(s,'m'))

    def test_alias_dictionary_on_complete_selected_population(self):
        from .exps import source_label_aliases
        from .utils import roster,RQ,read
        aliases=source_label_aliases();inverse={v:k for k,v in aliases.items()}
        self.assertEqual(len(inverse),len(aliases))
        for row in roster():
            evidence=read(RQ/'results/cpu_render_v6/population01/inputs'/row['id']/'S_JOINT/evidence.json')
            for card in evidence['cards']:
                for detail in card['data'].get('details',[]):
                    encoded=[aliases.get(s,s) for s in detail['name'].split(' · ')]
                    self.assertEqual(' · '.join(inverse.get(s,s) for s in encoded),detail['name'])

    def test_caption_value_changes_and_lost_occurrence_rejected(self):
        from .exps import xs_caption_audit
        from .utils import save
        from tempfile import TemporaryDirectory
        from pathlib import Path
        evidence={'cards':[{'id':'MET1','data':{'details':[{'name':'current','value':'0.00'}]}}]}
        with TemporaryDirectory() as d:
            p=Path(d);save(p/'readability.json',{'prefixes':[{'binding':'MET1.detail.0','name':'cur','value':'0.00'}]})
            self.assertEqual(xs_caption_audit(evidence,p)['occurrences'],1)
            save(p/'readability.json',{'prefixes':[{'binding':'MET1.detail.0','name':'cur','value':'0'}]})
            with self.assertRaises(ValueError):xs_caption_audit(evidence,p)
            save(p/'readability.json',{'prefixes':[]})
            with self.assertRaises(ValueError):xs_caption_audit(evidence,p)

    def test_anchor_withdrawal_reference(self):
        import numpy as np
        from .exps import predict_anchor_offsets
        a=np.zeros((64,128),dtype=np.uint8);a[10:12,25:34]=1;a[49,100]=1
        dom={'blocks':[{'id':'A0','box':[24,8,12,8]}]}
        self.assertEqual(predict_anchor_offsets(a,dom,[]),[0,1,7])
        self.assertEqual(predict_anchor_offsets(a,dom,[{'id':'A0','dx':-8,'dy':0}]),[0,7])

    def test_prompt_has_only_fixed_label_dictionary(self):
        from .exps import xs_prompt
        p='TASK<|im_end|>\n<|im_start|>assistant'
        result=xs_prompt(p)
        self.assertTrue(result.endswith('<|im_start|>assistant'))
        self.assertNotIn('INC-',result)
        with self.assertRaises(ValueError):xs_prompt('wrong boundary')


class CacheAdmissionRegression(unittest.TestCase):
    @staticmethod
    def config():
        import torch
        from vllm.v1.kv_cache_interface import KVCacheConfig,KVCacheGroupSpec,FullAttentionSpec,MambaSpec
        # Same hybrid group structure; small head dimensions, no model allocation.
        full=FullAttentionSpec(block_size=784,num_kv_heads=1,head_size=1,dtype=torch.bfloat16)
        mamba=MambaSpec(block_size=40960,shapes=((1568,),),dtypes=(torch.bfloat16,),mamba_cache_mode='none')
        return KVCacheConfig(285,[],[KVCacheGroupSpec(['full'],full)]+
            [KVCacheGroupSpec(['linear'+str(i)],mamba) for i in range(3)])

    def test_real_native_allocator_and_full_output_reservation(self):
        import asyncio
        from vllm import SamplingParams
        from vllm.v1.request import Request
        from vllm.v1.core.kv_cache_manager import KVCacheManager
        from .utils import vllm_cache_profile,VLLMCacheAdmission
        cfg=self.config();profile=vllm_cache_profile(cfg);gate=VLLMCacheAdmission(profile)
        self.assertEqual(profile['usable_blocks'],284)
        lengths=[23494,29120,29978,31423,31147,29252,28707,27542]
        self.assertGreater(sum(gate.cost(n) for n in lengths),gate.capacity)
        block=__import__('math').lcm(784,40960)
        manager=KVCacheManager(cfg,40960,block,block,enable_caching=False)
        # The original eight long requests cannot fit, even before output growth.
        failed=False
        for i,n in enumerate(lengths):
            req=Request(str(i),[1]*n,SamplingParams(max_tokens=8192),None)
            if manager.allocate_slots(req,n) is None:failed=True;break
        self.assertTrue(failed)
        async def exercise():
            manager=KVCacheManager(cfg,40960,block,block,enable_caching=False);active=[]
            for i,n in enumerate(lengths):
                if gate.used+gate.cost(n)>gate.capacity:break
                await gate.acquire(str(i),n)
                req=Request(str(i),[1]*n,SamplingParams(max_tokens=8192),None);active.append(req)
                self.assertIsNotNone(manager.allocate_slots(req,n+8192))
            used=284-manager.block_pool.get_num_free_blocks()
            self.assertEqual(used,gate.used)
            for req in active:manager.free(req);await gate.release(req.request_id)
            self.assertEqual(gate.used,0);self.assertEqual(manager.block_pool.get_num_free_blocks(),284)
        asyncio.run(exercise())

    def test_fifo_capacity_cancel_and_eight_visual_requests(self):
        import asyncio
        from .utils import vllm_cache_profile,VLLMCacheAdmission
        async def exercise():
            gate=VLLMCacheAdmission(vllm_cache_profile(self.config()))
            for i in range(8):await gate.acquire(str(i),12000)
            self.assertEqual(len(gate.active),8)
            first=asyncio.create_task(gate.acquire('long',32768));await asyncio.sleep(0)
            second=asyncio.create_task(gate.acquire('next',32768));await asyncio.sleep(0)
            self.assertFalse(first.done());self.assertFalse(second.done())
            first.cancel()
            with self.assertRaises(asyncio.CancelledError):await first
            for i in range(8):await gate.release(str(i))
            await asyncio.wait_for(second,1);await gate.release('next')
            self.assertEqual(gate.snapshot()['reserved_blocks'],0);self.assertEqual(gate.waiters,[])
            with self.assertRaises(ValueError):await gate.acquire('bad',32769)
            with self.assertRaises(ValueError):gate.cost(1,8191)
            gate.capacity=1
            with self.assertRaises(ValueError):await gate.acquire('too_large',1000)
        asyncio.run(exercise())

    def test_guarded_future_death_deadline_and_original_exception(self):
        from concurrent.futures import Future
        from types import SimpleNamespace as NS
        from .exps import VLLMSolvers
        solver=VLLMSolvers.__new__(VLLMSolvers)
        solver.thread=NS(is_alive=lambda:True);solver.engine=NS(errored=True);solver.deadline=None
        future=Future()
        with self.assertRaisesRegex(RuntimeError,'engine died'):solver.await_request(future,.001)
        self.assertTrue(future.cancelled())
        solver.engine.errored=False;solver.deadline=0;future=Future()
        with self.assertRaises(TimeoutError):solver.await_request(future,.001)
        future=Future();future.set_exception(TimeoutError('original RPC error'))
        with self.assertRaisesRegex(TimeoutError,'original RPC error'):solver.await_request(future,.001)
        future=Future();future.set_result('complete')
        self.assertEqual(solver.await_request(future),'complete')

    def test_dead_engine_skips_cleanup_rpc_and_releases_reservation(self):
        import asyncio,time
        from types import SimpleNamespace as NS
        from .utils import vllm_cache_profile,VLLMCacheAdmission
        from .exps import VLLMSolvers
        async def exercise():
            solver=VLLMSolvers.__new__(VLLMSolvers);solver.admission=VLLMCacheAdmission(vllm_cache_profile(self.config()))
            class Engine:
                errored=False
                async def collective_rpc(self,*a,**kw):
                    if self.errored:raise AssertionError('Cleanup RPC on dead engine')
                    self.errored=True;raise RuntimeError('engine died during encode')
            solver.engine=Engine()
            with self.assertRaisesRegex(RuntimeError,'engine died during encode'):
                await solver._request({'identity':'test'},{'metadata':{'length':9000},'batch':{}},time.monotonic())
            self.assertEqual(solver.admission.used,0)
        asyncio.run(exercise())


class VLLMBackendRegression(unittest.TestCase):
    def test_real_rpc_binary_roundtrip(self):
        import torch
        from vllm.v1.serial_utils import MsgpackEncoder,MsgpackDecoder
        from .utils import vllm_tensor_wire,vllm_tensor_unwire
        for dtype in (torch.int64,torch.float32,torch.bfloat16):
            original=torch.arange(2400,dtype=dtype).reshape(40,60)
            envelope={'batch':{'value':vllm_tensor_wire(original)}}
            received=MsgpackDecoder().decode(MsgpackEncoder().encode(envelope))
            restored=vllm_tensor_unwire(received['batch']['value'])
            self.assertTrue(torch.equal(original,restored));self.assertEqual(dtype,restored.dtype)
            reply=MsgpackDecoder().decode(MsgpackEncoder().encode([vllm_tensor_wire(restored)]))
            self.assertTrue(torch.equal(original,vllm_tensor_unwire(reply[0])))
            damaged=dict(reply[0],shape=[2401])
            with self.assertRaises(ValueError):vllm_tensor_unwire(damaged)

    @staticmethod
    def metadata(mode='U',n=24):
        return {'schema':'RQ43VLLMPromptV13','length':n,'positions':[list(range(n)) for _ in range(3)],
            'rope_delta':0,'operation':mode,'groups':[list(range(3,11)),list(range(11,19))],
            'image_start':3,'image_count':16,'attention':None,'task':'RCA'}

    def test_metadata_rejects_unknown_and_invalid_geometry(self):
        import copy
        from .utils import validate_vllm_metadata
        meta=self.metadata();self.assertIs(validate_vllm_metadata(meta),meta)
        for field,value in [('private_label','bad'),('rope_delta',9),('operation','new'),('groups',[[1,2]])]:
            altered=copy.deepcopy(meta);altered[field]=value
            with self.assertRaises(ValueError):validate_vllm_metadata(altered)

    def test_normalized_delta_matches_original_all_directions(self):
        import torch
        from .exps import vllm_grouped_delta
        from transformers.models.qwen3_5.modeling_qwen3_5 import l2norm
        torch.manual_seed(173);q=torch.randn(1,35,2,8);k=torch.randn_like(q);v=torch.randn(1,35,2,12)
        g=-torch.rand(1,35,2);beta=torch.sigmoid(torch.randn(1,35,2));groups=[list(range(3,13)),list(range(20,35))]
        for direction in (True,False):
            expected=grouped_delta(q,k,v,g,beta,groups,direction)
            actual=vllm_grouped_delta(l2norm(q),l2norm(k),v,g,beta,groups,direction)
            torch.testing.assert_close(expected,actual,rtol=1e-6,atol=1e-6)
        v=torch.randn(1,35,6,12);g=-torch.rand(1,35,6);beta=torch.sigmoid(torch.randn(1,35,6))
        for direction in (True,False):
            expected=grouped_delta(q.repeat_interleave(3,dim=2),k.repeat_interleave(3,dim=2),v,g,beta,groups,direction)
            actual=vllm_grouped_delta(l2norm(q),l2norm(k),v,g,beta,groups,direction)
            torch.testing.assert_close(expected,actual,rtol=1e-6,atol=1e-6)

    def test_same_schema_compiled_grammar_accepted_by_native_validator(self):
        import xgrammar as xgr
        from .utils import rca_schema
        from vllm import SamplingParams
        from vllm.sampling_params import StructuredOutputsParams
        from vllm.v1.structured_output.backend_xgrammar import validate_xgrammar_grammar
        grammar=str(xgr.Grammar.from_json_schema(rca_schema(True),any_whitespace=False))
        self.assertIn('root ::=',grammar)
        validate_xgrammar_grammar(SamplingParams(structured_outputs=StructuredOutputsParams(grammar=grammar)))

    def test_ranking_batch_removal_reorder_and_qa(self):
        import torch
        from types import SimpleNamespace
        from .utils import RQ43RankingProcessor
        from vllm.v1.sample.logits_processor.interface import BatchUpdate,MoveDirectionality
        p=RQ43RankingProcessor.__new__(RQ43RankingProcessor);p.states={}
        p.tokenizer=SimpleNamespace(decode=lambda ids,**kw:''.join(map(chr,ids)))
        a=[];b=list(map(ord,'{"services":["123","456","789","234","567"]'))
        rca=SimpleNamespace(extra_args={'canvasrca':{'task':'RCA'}});qa=SimpleNamespace(extra_args={'canvasrca':{'task':'QA'}})
        p.update_state(BatchUpdate(3,[],[(0,rca,None,a),(1,rca,None,b),(2,qa,None,[])],[]))
        original=torch.randn(3,11);result=p.apply(original.clone())
        self.assertEqual(torch.isfinite(result[0]).sum().item(),1)
        torch.testing.assert_close(result[1:],original[1:])
        p.update_state(BatchUpdate(2,[1],[],[(0,1,MoveDirectionality.UNIDIRECTIONAL)]))
        self.assertEqual(set(p.states),{1});self.assertIs(p.states[1]['tokens'],a)
        a.extend(map(ord,'{"services":[]}'));result=p.apply(original[:2].clone())
        torch.testing.assert_close(result,original[:2])

    def test_installed_worker_branches_preserve_state_and_request_boundaries(self):
        import torch,copy
        from types import SimpleNamespace as NS
        from .exps import VLLMWorkerExtension,vllm_grouped_delta
        from transformers.models.qwen3_5.modeling_qwen3_5 import l2norm
        torch.manual_seed(197)
        class Chunk:
            def forward(self,**kw):return kw['v'].clone(),kw['initial_state'].clone()
        class Projection:
            def __init__(self,in_dim,out_dim):self.weight=torch.randn(in_dim,out_dim)*.1
            def __call__(self,x):return x@self.weight,None
        full=NS(num_heads=2,num_kv_heads=1,head_dim=4,qkv_proj=Projection(20,24),o_proj=Projection(8,20))
        def project(x,positions):return x[:,:8],x[:,8:12],x[:,12:16],x[:,16:]
        full._project_qkv_gate=project
        worker=VLLMWorkerExtension();layers=[NS(linear_attn=NS(chunk_gated_delta_rule=Chunk())) for _ in range(3)]+[NS(self_attn=full)]
        model=NS(language_model=NS(model=NS(layers=layers)),forward=lambda *a,**k:None)
        runner=NS(get_model=lambda:model,_init_mrope_positions=lambda req:None,execute_model=lambda *a,**kw:None)
        worker.model_runner=runner;worker.vllm_config=NS(model_config=NS(dtype=torch.bfloat16),parallel_config=NS(tensor_parallel_size=1),
            scheduler_config=NS(enable_chunked_prefill=False),cache_config=NS(enable_prefix_caching=False))
        with tempfile.TemporaryDirectory() as folder:
            worker.rq43_install(folder);state=worker._rq43_state
            def attention(q,k,v):
                out=torch.empty_like(q)
                for rec in state['records']:
                    sl=slice(rec['start'],rec['end']);n=rec['end']-rec['start']
                    qq=q[sl].view(n,2,4).transpose(0,1)[None];kk=k[sl].view(n,1,4).transpose(0,1)[None]
                    vv=v[sl].view(n,1,4).transpose(0,1)[None]
                    out[sl]=torch.nn.functional.scaled_dot_product_attention(qq,kk.repeat_interleave(2,1),vv.repeat_interleave(2,1),is_causal=True)[0].transpose(0,1).reshape(n,8)
                return out
            full.attn=attention
            try:
                for mode in ('U','P_LOCAL_BI','P_SOFT_IMAGE','P_DUAL','C_LOCAL_FORWARD','C_SHAM_BI','C_GLOBAL_BI'):
                    state['records']=[{'key':'a','start':0,'end':24,'prefill':True,'meta':self.metadata(mode)},
                        {'key':'b','start':24,'end':48,'prefill':True,'meta':self.metadata('U')}]
                    state['requests']={x:{'branch_calls':0,'tap':None} for x in ('a','b')}
                    q=l2norm(torch.randn(1,48,2,4));k=l2norm(torch.randn_like(q));v=torch.randn_like(q)
                    g=-torch.rand(1,48,2);beta=torch.rand(1,48,2);initial=torch.randn(2,2,4,4)
                    for layer in layers[:3]:
                        actual,last=layer.linear_attn.chunk_gated_delta_rule.forward(q=q,k=k,v=v,g=g,beta=beta,
                            initial_state=initial,use_qk_l2norm_in_kernel=False)
                        torch.testing.assert_close(last,initial);torch.testing.assert_close(actual[:,24:],v[:,24:])
                        expected=v.clone();groups=self.metadata()['groups']
                        if mode=='C_GLOBAL_BI':groups=[sum(groups,[])]
                        if mode not in {'U','P_SOFT_IMAGE'}:
                            aux=vllm_grouped_delta(q[:,:24],k[:,:24],v[:,:24],g[:,:24],beta[:,:24],groups,mode!='C_LOCAL_FORWARD')
                            ids=sum(groups,[]);expected[:,ids]=.75*v[:,ids]+.25*aux[:,ids]
                        torch.testing.assert_close(actual,expected)
                    hidden=torch.randn(48,20);packed=full.qkv_proj(hidden)[0];qq,kk,vv,gate=project(packed,None)
                    expected=attention(qq,kk,vv)
                    if mode in {'P_SOFT_IMAGE','P_DUAL'}:
                        q4=qq[:24].view(24,2,4).transpose(0,1)[None]
                        k4=kk[:24].view(24,1,4).transpose(0,1)[None].repeat_interleave(2,1)
                        v4=vv[:24].view(24,1,4).transpose(0,1)[None].repeat_interleave(2,1)
                        expected[:24]=soft_image_reference(q4,k4,v4,list(range(3,19)),3)[0].transpose(0,1).reshape(24,8)
                    expected=full.o_proj(expected*torch.sigmoid(gate))[0];output=torch.empty_like(expected)
                    full.forward(None,output,hidden);torch.testing.assert_close(output,expected,rtol=1e-5,atol=1e-6)
                    counts={'U':0,'P_LOCAL_BI':3,'P_SOFT_IMAGE':1,'P_DUAL':4,'C_LOCAL_FORWARD':3,'C_SHAM_BI':3,'C_GLOBAL_BI':3}
                    self.assertEqual(state['requests']['a']['branch_calls'],counts[mode]);self.assertEqual(state['requests']['b']['branch_calls'],0)
                state['requests'].clear()
            finally:worker.rq43_shutdown()


def vllm_offline_qualification():
    """Targeted real input and synthetic algebra checks; zero model requests."""
    import io,time,torch
    from types import SimpleNamespace,MethodType
    from transformers import AutoProcessor,AutoConfig
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5Model
    from RQs.RQ4_1.src.utils import pack_injected_batch
    from .utils import RQ,vllm_prompt_packet,stable
    stream=io.StringIO();suite=unittest.TestSuite()
    for cls in (CacheAdmissionRegression,VLLMBackendRegression,HostSchedulingRegression,RuntimeRegression):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    folder=RQ/'results/deployment_v13';(folder/'offline_unit.log').write_text(stream.getvalue());print(stream.getvalue(),flush=True)
    if not result.wasSuccessful():raise RuntimeError('vLLM isolated regression failed')
    processor=AutoProcessor.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    cfg=AutoConfig.from_pretrained('/home/lglsj/CanvasRCA/models/Qwen3.8-27B',local_files_only=True)
    shell=SimpleNamespace(config=cfg);shell.get_vision_position_ids=MethodType(Qwen3_5Model.get_vision_position_ids,shell)
    queue=read(folder/'queue.json')['items'];selected={}
    for item in queue:
        req=read(ROOT/item['request'])
        key=(item['dataset'],req['operation'],req['task'],'order' if req['order'] else 'regular')
        selected.setdefault(key,(item,req))
        if not req['image']:selected.setdefault(('long_text',),(item,req))
    # Frozen registration renders predate measured header anchors. Use actual
    # committed, freshly rendered inputs to check attention geometry as well.
    item_by_key={i['key']:i for i in queue}
    for path in sorted((RQ/'results/formal_v7/execution/completed').glob('*.json')):
        done=read(path);item=item_by_key[path.stem]
        if not done.get('request_path'):continue
        req=read(RQ/'results/formal_v7/execution'/done['request_path'])
        if req['image'] and 'header' in read(ROOT/req['manifest']).get('audit',{}):
            selected.setdefault((item['dataset'],'actual_attention'),(item,req))
    records=[]
    for key,(item,req) in selected.items():
        tick=time.monotonic();req=dict(req)
        req['attention']=bool(req['image'] and 'header' in read(ROOT/req['manifest']).get('audit',{}))
        packet=vllm_prompt_packet(req,processor);batch=packet['batch'];n=batch['input_ids'].shape[1]
        embeddings=torch.arange(n,dtype=torch.float64)[None,:,None].repeat(1,1,4)
        if req['image']:
            mm=(batch['input_ids']==cfg.image_token_id).long()
            original,_=Qwen3_5Model.get_rope_index(shell,batch['input_ids'],mm,image_grid_thw=batch['image_grid_thw'],attention_mask=torch.ones_like(mm))
            visual=torch.arange(len(packet['image_positions']),dtype=torch.float64)[:,None].repeat(1,4)+100000
            legacy=pack_injected_batch(batch['input_ids'],torch.ones_like(mm),original,embeddings,[visual],cfg.image_token_id,[req['retained']])
            if req['order']:
                legacy['inputs_embeds'],legacy['position_ids'],legacy['rope_deltas']=reorder_visual_prefix(
                    legacy['inputs_embeds'],legacy['position_ids'],req['groups'],packet['metadata']['image_start'],legacy['rope_deltas'])
            current=embeddings[0].clone();current[packet['image_positions']]=visual
            current=current[packet['keep']][packet['source_by_slot']]
            torch.testing.assert_close(current,legacy['inputs_embeds'][0],rtol=0,atol=0)
            torch.testing.assert_close(torch.tensor(packet['metadata']['positions']),legacy['position_ids'][1:,0],rtol=0,atol=0)
            if packet['metadata']['rope_delta']!=int(legacy['rope_deltas'][0,0]):raise ValueError('Historical MRoPE continuation changed')
        elif packet['metadata']['positions']!=[list(range(n))]*3:raise ValueError('Text positions changed')
        records.append({'key':item['key'],'dataset':item['dataset'],'operation':req['operation'],'task':req['task'],
            'order':req['order'],'attention':req['attention'],'actual_input_tokens':packet['metadata']['length'],'status':'passed','seconds':time.monotonic()-tick})
        save(folder/'offline_packet_progress.json',{'completed':len(records),'total':len(selected),'records':records})
        print('v13 CPU packet',len(records),'/',len(selected),item['key'],flush=True)
        del packet,batch,embeddings
    if len({r['dataset'] for r in records if r['attention']})!=3:raise RuntimeError('Actual attention geometry did not cover all datasets')
    return {'status':'passed','synthetic_tests':result.testsRun,'actual_packets':len(records),'records':records,
        'new_model_calls':0,'real_model_numerical_equivalence':'not_tested','scope':'targeted_backend_translation_and_batch_algebra'}


def run_tests(integration=False):
    import io
    stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Prerequisites)
    if integration:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(FrozenVisualInputRegression))
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(PrefillIntegration))
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(SelectionRegression))
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeRegression))
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(XSRPRegression))
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    print(stream.getvalue(),flush=True)
    return {'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'details':stream.getvalue(),
        'scope':'prerequisite_unit_regressions_only','full_cpu_qualified':False}

class RestorationRegression(unittest.TestCase):
    def test_visible_aliases_invert_all_public_occurrences(self):
        from .utils import roster
        from .exps import r14_aliases,r14_prompt,source_label_aliases
        aliases=r14_aliases();inverse={v:k for k,v in aliases.items()};count=0
        for row in roster():
            for card in read(ROOT/row['base']/'evidence.json')['cards']:
                for item in card['data'].get('details',[]):
                    encoded=[aliases.get(s,s) for s in item['name'].split(' · ')]
                    self.assertEqual(' · '.join(inverse.get(s,s) for s in encoded),item['name']);count+=1
        self.assertGreater(count,10000)
        prompt='task<|im_end|>\n<|im_start|>assistant'
        self.assertIn('two folded magnitude bands',r14_prompt(prompt))
        with self.assertRaises(ValueError):r14_prompt('unknown interface')

    def test_phase_path_independent_public_grammar(self):
        import json,subprocess
        from .utils import roster
        from .exps import r14_caption_name
        from renderer.main import node_runtime
        web=ROOT/'src/renderer/web';names=sorted({d['name'] for row in roster() for c in read(ROOT/row['base']/'evidence.json')['cards'] for d in c['data'].get('details',[])})
        source="import {phasePath} from './components/PackedDetails.tsx';import {captionName} from './components/PackedSource.tsx';console.log(JSON.stringify("+json.dumps(names)+".map(n=>phasePath(captionName(n)).join(' · '))));"
        built=subprocess.run([str(web/'node_modules/esbuild/bin/esbuild'),'--bundle','--platform=node','--format=cjs','--packages=external','--loader=tsx'],input=source,text=True,cwd=web,capture_output=True,check=True)
        out=subprocess.run([str(node_runtime()),'-e',built.stdout],cwd=web,text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(out.stdout),[r14_caption_name(n) for n in names])
        self.assertEqual(len(set(json.loads(out.stdout))),len(names))


    def test_background_replacement_exact_budget_and_support(self):
        from .exps import r14_background_control
        support={'anchors':[0,1],'image_tokens':12,'roles':{'a':{'foreground_possible_tokens':[2,3,4,5]}}}
        retained={'indices':[0,1,2,3,4,5],'optional_order':[2,3,4,5]}
        a=r14_background_control(support,retained,2,'fixture')
        self.assertTrue(a['qualified']);self.assertEqual(a['D'],2);self.assertEqual(len(a['indices']),6)
        self.assertEqual(set(a['indices'])&set(range(6)),{0,1,2,3});self.assertEqual(a['observed_extra_fraction'],1)
        self.assertEqual(a,r14_background_control(support,retained,2,'fixture'))
        b=r14_background_control(dict(support,image_tokens=6),retained,2,'fixture')
        self.assertFalse(b['qualified']);self.assertEqual(b['indices'],retained['indices'])
        self.assertFalse(r14_background_control(support,retained,4,'fixture')['qualified'])

    def test_offset_keeps_content_and_canvas(self):
        from .exps import r14_offset_design
        x={'viewport':{'width':1056,'height':1024},'tree':{'id':'gutter','type':'row','weights':[1024,32],
            'children':[{'id':'content','type':'panel','card':'a'},{'id':'right','type':'spacer'}]}}
        y=r14_offset_design(x)
        self.assertEqual(y['viewport'],x['viewport']);self.assertEqual(y['tree'],x['tree'])
        self.assertEqual(y['raster_translation']['dx'],16);self.assertEqual(x['tree']['weights'],[1024,32])
        x['tree']['weights'][-1]=16
        with self.assertRaises(ValueError):r14_offset_design(x)

    def test_layout_does_not_drop_or_duplicate_sources(self):
        from .exps import r14_layouts,r14_offset_design
        from renderer.utils import compile_design
        from .utils import roster
        row=roster()[0];base=ROOT/row['base'];e=read(base/'evidence.json');d=read(base/'design.json')
        # Actual layout compiler is tested on synthetic DOM dimensions; real DOM
        # readability and source bindings are independently checked in population.
        cards=[{'card':c['id'],'height':256,'width':1024,'overflow':[],'min_font':18} for c in e['cards']]
        out=r14_layouts(e,d,{'measurements':[{'region_width':1024,'cards':cards}]},100000)
        good=[x for x in out if x['pass']];self.assertTrue(good)
        got=good[0];self.assertEqual(got['width']%32,0)
        def ids(n):return ([n['card']] if n['type']=='panel' else [])+sum((ids(c) for c in n.get('children',[])),[])
        self.assertCountEqual(ids(got['design']['tree']),[c['id'] for c in e['cards']])
        bad=[dict(c,min_font=17) for c in cards]
        self.assertFalse(any(x['pass'] for x in r14_layouts(e,d,{'measurements':[{'region_width':1024,'cards':bad}]},100000)))

    def test_horizon_component_extremes_zero_and_missing(self):
        import subprocess,json,os
        from renderer.main import node_runtime
        web=ROOT/'src/renderer/web'
        source="""import React from 'react';import {renderToStaticMarkup} from 'react-dom/server';
import Horizon,{horizonBand} from './components/MetricHorizon.tsx';
const cases=[[0,0],[null,0,null],[-10,0,10],[1e-9,1e9],[-3,null,3],[4],[null,null]];
console.log(JSON.stringify(cases.map(v=>({v,b:horizonBand(v),html:renderToStaticMarkup(React.createElement(Horizon,{card:{id:'M',kind:'metric',title:'signal',entity:'123',unit:'ms',data:{values:v,bins:v.map((_,i)=>i*3),details:[]}},rect:{}}))}))));"""
        built=subprocess.run([str(web/'node_modules/esbuild/bin/esbuild'),'--bundle','--platform=node',
            '--format=cjs','--packages=external','--loader=tsx'],input=source,text=True,cwd=web,capture_output=True,check=True)
        output=subprocess.run([str(node_runtime()),'-e',built.stdout],cwd=web,text=True,capture_output=True,check=True)
        import xml.etree.ElementTree as ET,math
        for record in json.loads(output.stdout):
            vals=record['v'];maximum=max([abs(v) for v in vals if v is not None]+[0]);b=record['b']
            if maximum==0:self.assertEqual(b,1)
            else:
                candidates=[k*10.**j for j in range(-12,14) for k in (1,2,5) if 2*k*10.**j>=maximum]
                self.assertAlmostEqual(b,min(candidates))
            dom=ET.fromstring('<root>'+record['html']+'</root>')
            points=[x.attrib['data-binding'] for x in dom.iter('circle')]
            self.assertEqual(points,['M.sample.'+str(i) for i,v in enumerate(vals) if v is not None])
            text=''.join(dom.itertext());self.assertIn('2b =',text)
            self.assertNotIn('NaN',record['html']);self.assertNotIn('?',text)


class DirectRetentionRegression(unittest.TestCase):
    def test_publish_keeps_actual_image_but_not_scratch_masks(self):
        from . import utils
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp);(d/'dashboard.png').write_bytes(b'actual pixels')
            (d/'anchor_foreground.png').write_bytes(b'temporary support');(d/'region_0.png').write_bytes(b'aux')
            save(d/'request.json',{'image':str(d/'region_0.png'),'manifest':str(d/'manifest.json')})
            save(d/'manifest.json',{'status':'passed'});(d/'dashboard.html').write_text('<html>complete</html>')
            kept=utils.durable_input_paths(d)
            self.assertIn(d/'region_0.png',kept);self.assertIn(d/'dashboard.png',kept)
            self.assertNotIn(d/'anchor_foreground.png',kept);self.assertIn(d/'dashboard.html',kept)

    def test_exact_dedup_preserves_paths_bytes_and_external_sources(self):
        from .utils import deduplicate_direct_files
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'results';out.mkdir();a=root/'outside';b=out/'inside';c=out/'different'
            a.write_bytes(b'\x00 complete bytes');b.write_bytes(a.read_bytes());c.write_bytes(b'other')
            self.assertEqual(deduplicate_direct_files({a,b,c},out),1)
            self.assertTrue(a.samefile(b));self.assertEqual(c.read_bytes(),b'other')
            self.assertEqual(deduplicate_direct_files({a,b,c},out),0)

    def test_finalization_preserves_complete_conversation_and_is_resumable(self):
        import sqlite3
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory() as temp:
            project=Path(temp);rq=project/'RQs/RQ4_3';root=rq/'results/formal_v7';ex=root/'execution'
            ex.mkdir(parents=True);data=rq/'results/cache';data.mkdir()
            image=data/'dashboard.png';image.write_bytes(b'original image binary')
            (data/'dashboard.html').write_text('<html>original labels</html>')
            save(data/'manifest.json',{'width':32,'height':32})
            (data/'anchor_foreground.png').write_bytes(b'unneeded mask')
            req={'prompt':'exact prompt\nwith newlines','image':str(image.relative_to(project)),
                'manifest':str((data/'manifest.json').relative_to(project)), 'operation':'U','order':False,
                'retained':[0],'groups':{},'processor':{}}
            save(ex/'requests/a.json',req);save(ex/'trajectories/a.json',{'response':'INVALID original output \" & < >'})
            committed={'request_hash':'frozen','attempt_id':1,'actual_calls':1,'request_path':'requests/a.json',
                'response':'INVALID original output \" & < >','artifact_hashes':{'trajectories/a.json':utils.digest(ex/'trajectories/a.json')}}
            save(ex/'completed/a.json',committed)
            q={'items':[{'id':'case','task':'RCA','key':'a','identity':'frozen','request':str((ex/'requests/a.json').relative_to(project))}]}
            path=rq/'results/queue.json';save(path,q)
            save(root/'phase_complete.json',{'writers_drained':True,'queue_sha256':utils.digest(path)})
            with sqlite3.connect(ex/'calls.sqlite') as db:
                db.execute('CREATE TABLE calls (id INTEGER,state TEXT)');db.execute("INSERT INTO calls VALUES(1,'complete')")
            att=root/'attention/passive.json';save(att,{'image_mass':.8,'text_mass':.2})
            code=project/'src/vlmrca/vlm/passive_summary.py';code.parent.mkdir(parents=True);code.write_text('# measured definition')
            with patch.object(utils,'ROOT',project),patch.object(utils,'RQ',rq),patch.object(utils,'queue_path',return_value=path),patch.object(utils,'score_context',return_value={'accepted':['service'] } ):
                a=utils.finalize_direct_results(root,q);self.assertEqual(a['status'],'passed')
                self.assertTrue(image.exists());self.assertTrue(att.exists());self.assertFalse((data/'anchor_foreground.png').exists())
                self.assertEqual(read(ex/'completed/a.json'),committed)
                out=project/'view.html';utils.view_conversation('a',out,root)
                self.assertIn('INVALID original output',out.read_text());self.assertIn('data:image/png;base64,',out.read_text())
                b=utils.finalize_direct_results(root,q);self.assertEqual(b['status'],'passed')
                self.assertFalse(list(rq.rglob('*.gz')));self.assertFalse(list(rq.rglob('*.zip')))
                save(ex/'completed/a.json',{**committed,'request_hash':'bad'})
                with self.assertRaises(ValueError):utils.finalize_direct_results(root,q)
                self.assertTrue(image.exists())

    def test_linked_html_is_exact_and_survives_interruption(self):
        from . import utils
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);assets=root/'styles';page=root/'case/dashboard.html';page.parent.mkdir()
            original='<html><head><style data-kind="font">body{color:red}</style><style>.a{font-size:18px}</style></head><body>0.0001 &amp; entity</body></html>'
            page.write_text(original)
            with patch.object(utils,'ROOT',root):
                kept=utils.externalize_html_styles(page,assets)
                self.assertIn('<link rel="stylesheet"',page.read_text());self.assertEqual(utils.original_html(page),original)
                meta=page.with_suffix('.storage.json');info=read(meta);meta.rename(meta.with_suffix('.pending.json'))
                self.assertEqual(utils.externalize_html_styles(page,assets),kept)
                self.assertEqual(utils.original_html(page),original)
                (root/info['styles'][0]['css']).write_text('changed')
                with self.assertRaises(ValueError):utils.original_html(page)
