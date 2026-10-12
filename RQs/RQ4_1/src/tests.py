"""Independent synthetic CPU contracts; no serving, GPU, or model calls."""
import itertools
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
import numpy as np
from .utils import (AttentionStore, coefficients, decode_sequence, objective, foreground_support, quota_targets, support_saturation,
                    save_json, read_json, select_tokens, stable_hash, evidence_budget, fit_rewire_bins, matched_rewire,select_registered_condition)
from .exps import ledger, compile_case, comparison_provenance, SOURCE, VISUAL_TASK


class RankingDecoder(unittest.TestCase):
    @staticmethod
    def fixture():
        import torch
        from .utils import RankingPrefixGreedy
        class Tokens:
            def decode(self,values,**kwargs):return ''.join(chr(x) for x in values)
        return RankingPrefixGreedy(Tokens()),lambda text:torch.tensor([[ord(x) for x in text]],dtype=torch.long)

    def test_generated_boundary_escaping_and_prompt_isolation(self):
        from .utils import ranking_array_complete
        self.assertFalse(ranking_array_complete('{"reason":"x","services":[]}'))
        self.assertFalse(ranking_array_complete('{"services":["1]00"'))
        self.assertFalse(ranking_array_complete('{"services":["x\\\"]"'))
        self.assertTrue(ranking_array_complete(' {"services":["100","101"] ,"reason":'))
        import torch
        adapter,ids=self.fixture();scores=torch.tensor([[1.,3.,2.]])
        prompt='static prompt {"services":["100","101","102","103","104"]}'
        masked=adapter(ids(prompt),scores)
        self.assertEqual(masked.argmax(-1).item(),1)
        self.assertEqual(torch.isfinite(masked).sum().item(),1)
        self.assertTrue(torch.equal(scores,torch.tensor([[1.,3.,2.]])))
        suffix='{"services":["100","101","102","103","104"]'
        self.assertIs(adapter(ids(prompt+suffix),scores),scores)
        self.assertIs(adapter(ids(prompt+suffix+',"reason":"text'),scores),scores)
        self.assertEqual(adapter.audit()['release_generated_tokens'],len(suffix))
        self.assertEqual(adapter.forced_steps,1)

    def test_after_grammar_before_sampling_and_release(self):
        import torch
        from transformers import TemperatureLogitsWarper,TopPLogitsWarper
        # A grammar masks the otherwise largest logit. Tie behavior equals
        # torch.argmax; subsequent temperature/top-p cannot change that ID.
        scores=torch.tensor([[2.,float('-inf'),4.,4.]])
        adapter,ids=self.fixture();prompt=ids('static')
        forced=adapter(prompt,scores)
        warped=TopPLogitsWarper(.95)(prompt,TemperatureLogitsWarper(1.)(prompt,forced))
        for seed in (1,42,999):
            torch.manual_seed(seed)
            self.assertEqual(torch.multinomial(warped.softmax(-1),1).item(),2)
        released=adapter(ids('static{"services":["100","101","102","103","104"]'),scores)
        self.assertIs(released,scores)
        self.assertEqual(torch.isfinite(released).sum().item(),3)

    def test_batch_and_registration_fail_closed(self):
        import os,torch
        from unittest.mock import patch
        from . import gates
        adapter,ids=self.fixture()
        with self.assertRaises(ValueError):adapter(ids('x').expand(2,-1),torch.ones(2,4))
        cfg=read_json('RQs/RQ4_1/configs/gpu_smoke_v22_round05.json')
        with patch.dict(os.environ,{'CANVASRCA_RQ41_SMOKE_CONFIG':'unused'}),patch.object(gates,'read_json',return_value=cfg):
            self.assertEqual(gates.smoke_runtime_config()['ranking_decoder_profile'],adapter.profile)
            cfg['hf_groups'][0]['greedy']=True
            with self.assertRaises(ValueError):gates.smoke_runtime_config()
            cfg['hf_groups'][0]['greedy']=False;cfg['decoder_authority']='missing'
            with self.assertRaises(ValueError):gates.smoke_runtime_config()


class StaticIdentifierGrammar(unittest.TestCase):
    def test_inventory_rectangle_independent_pixels_and_fixed_budget(self):
        from .utils import inventory_context_protection
        m={'source_png':{'width':100,'height':100},'audit':{'bindings':[
            {'key':'INV002.title','x':20,'y':20,'width':20,'height':10},
            {'key':'INV002.identity.0','x':20,'y':35,'width':10,'height':10}]}}
        r=inventory_context_protection(m,(10,10),[99],21)
        self.assertEqual(r['protected_indices'],[11,12,13,14,21,22,23,24,31,32,33,34,41,42,43,44,51,52,53,54,99])
        self.assertEqual(r['optional_slots_remaining'],0)
        with self.assertRaises(ValueError):inventory_context_protection(m,(10,10),[99],20)
        with self.assertRaises(ValueError):inventory_context_protection(m,(10,10),[99],21,card_id='absent')

    def test_real_grammar_rejects_bad_syntax_without_candidate_enumeration(self):
        import xgrammar as xgr
        from .utils import rca_schema,rca_generation_schema
        info=xgr.TokenizerInfo([chr(i) for i in range(32,127)]+['<eos>'],stop_token_ids=[95])
        schema=rca_generation_schema('public_numeric_id_v23')
        grammar=xgr.GrammarCompiler(info,max_threads=2).compile_json_schema(schema,any_whitespace=False)
        def accepts(value):
            answer={'services':[value,'101','102','103','104'],'reason':'test','confidence':'low'}
            return xgr.GrammarMatcher(grammar,terminate_without_stop_token=True).accept_string(json.dumps(answer))
        for value in ('100','999','1000','9999','10000','99999'):self.assertTrue(accepts(value))
        for value in ('30','service_130','service 130','000','0123','100000','1e3',''):
            self.assertFalse(accepts(value),value)
        reversed_keys={'reason':'x','services':['100','101','102','103','104'],'confidence':'low'}
        self.assertFalse(xgr.GrammarMatcher(grammar,terminate_without_stop_token=True).accept_string(json.dumps(reversed_keys)))
        # The grammar accepts all identities in the static domain, including
        # unknown candidates; membership is still the unchanged host's job.
        self.assertNotIn('enum',schema['properties']['services']['items'])
        self.assertEqual(rca_generation_schema(),rca_schema())
        self.assertNotIn('pattern',rca_schema()['properties']['services']['items'])
        with self.assertRaises(ValueError):rca_generation_schema('per_case')

    def test_partial_smoke_capture_excludes_prompt_and_does_not_change_logits(self):
        import torch
        from .utils import SmokeLogitsCapture
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'progress.json';capture=SmokeLogitsCapture(path)
            scores=torch.tensor([[1.,2.,3.]])
            self.assertIs(capture(torch.tensor([[91,92,93]]),scores),scores)
            self.assertEqual(read_json(path)['generated_token_ids'],[[]])
            capture.step=128
            self.assertIs(capture(torch.tensor([[91,92,93]+list(range(128))]),scores),scores)
            self.assertEqual(read_json(path)['generated_token_ids'],[list(range(128))])
            self.assertTrue(torch.equal(scores,torch.tensor([[1.,2.,3.]])))


class PriorCompletion(unittest.TestCase):
    """New CPU checks only: frozen official oracles and real Qwen classes.

    Reduced random dimensions exercise architecture, not checkpoint accuracy.
    No actual diagnostic answer or old arm result is read.
    """
    @staticmethod
    def reference(name, suffix, function=None):
        import ast,sys,types
        base=Path('RQs/RQ4_1/results/comparison_coding_v1/prior_completion_v13/references')
        manifest=read_json(base/'manifest.json')
        row=next(r for r in manifest if r['method']==name and r['path'].endswith(suffix))
        from .utils import digest
        if digest(row['path'])!=row['sha256']:raise ValueError('Official reference changed')
        text=Path(row['path']).read_text()
        if function:
            tree=ast.parse(text);node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==function)
            code='from __future__ import annotations\n'+ast.unparse(node)
        else:code=text
        import torch,os
        module=types.ModuleType('_rq41_reference_'+name);sys.modules[module.__name__]=module
        module.__dict__.update(torch=torch,np=np,os=os)
        exec(compile(code,row['path'],'exec'),module.__dict__)
        return getattr(module,function) if function else module

    @staticmethod
    def tiny_model():
        import torch
        from unittest.mock import patch
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5TextConfig
        from transformers.models.qwen3_5 import modeling_qwen3_5 as m
        torch.manual_seed(130107);torch.set_num_threads(1)
        cfg=Qwen3_5TextConfig(hidden_size=32,intermediate_size=64,num_hidden_layers=4,
            num_attention_heads=4,num_key_value_heads=2,head_dim=8,vocab_size=97,
            layer_types=['linear_attention']*3+['full_attention'],linear_num_key_heads=2,
            linear_num_value_heads=4,linear_key_head_dim=8,linear_value_head_dim=8,
            linear_conv_kernel_dim=4,rope_parameters={'rope_type':'default','rope_theta':10000.,
                'partial_rotary_factor':1.,'mrope_section':[1,1,2],'mrope_interleaved':True})
        cfg._attn_implementation='sdpa'
        with patch.object(m,'FusedRMSNormGated',None):model=m.Qwen3_5TextModel(cfg).eval()
        for layer in model.layers:
            if layer.block_type=='linear_attention':
                layer.linear_attn.causal_conv1d_fn=None
                layer.linear_attn.causal_conv1d_update=m.torch_causal_conv1d_update
                layer.linear_attn.chunk_gated_delta_rule=m.torch_chunk_gated_delta_rule
                layer.linear_attn.recurrent_gated_delta_rule=m.torch_recurrent_gated_delta_rule
        return model

    def test_scope_matches_official_greedy(self):
        import torch,os
        from unittest.mock import patch
        from .utils import scope_select
        oracle=self.reference('scope','scope/clip_encoder.py','SCOPE')
        rng=np.random.default_rng(138)
        for size in (16,37):
            f=rng.normal(size=(size,13)).astype(np.float32);s=rng.uniform(.01,1,size).astype(np.float32)
            for k in (1,7,size):
                with patch.dict(os.environ,{'ALPHA':'1.0','COMBINED':'multi'}):
                    expected,_=oracle(torch.from_numpy(f)[None],k,torch.from_numpy(s)[None])
                actual=scope_select(f,s,k)
                self.assertEqual(actual['selection_order'],expected[0].tolist())
        self.assertEqual(scope_select(np.eye(8),np.zeros(8),4)['indices'],[0,1,2,3])

    def test_scope_rejects_missing_signal_and_bad_inputs(self):
        from .utils import scope_select
        for saliency in (None,[1,2],[-1,2,3], [1,float('nan'),3]):
            with self.assertRaises(ValueError):scope_select(np.eye(3),saliency,2)
        with self.assertRaises(ValueError):scope_select(np.zeros((3,4)),np.ones(3),2)
        with self.assertRaises(TimeoutError):scope_select(np.eye(3),np.ones(3),2,seconds=-1)

    def test_scope_actual_qwen_vision_signal_preserves_forward(self):
        import torch
        from .utils import ScopeVisionSignal
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
        from transformers.models.qwen3_5 import modeling_qwen3_5 as m
        torch.manual_seed(19);torch.set_num_threads(1)
        cfg=Qwen3_5VisionConfig(depth=3,hidden_size=32,intermediate_size=64,num_heads=4,
            out_hidden_size=32,patch_size=2,temporal_patch_size=1,spatial_merge_size=2,num_position_embeddings=16)
        cfg._attn_implementation='sdpa';vision=m.Qwen3_5VisionModel(cfg).eval()
        pixels=torch.randn(16,12);grid=torch.tensor([[1,4,4]]);expected=[]
        def dense(module,args,kwargs):
            x=args[0];q,k,_=module.qkv(x).reshape(len(x),3,module.num_heads,-1).permute(1,0,2,3).unbind(0)
            q,k=m.apply_rotary_pos_emb_vision(q,k,*kwargs['position_embeddings'])
            a=torch.softmax(torch.einsum('ihd,jhd->hij',q.float(),k.float())*module.scaling,dim=-1)
            expected.append(a.mean((0,1)).reshape(-1,4).sum(1))
        with torch.no_grad():
            native=vision(pixels,grid_thw=grid).pooler_output
            handle=vision.blocks[-2].attn.register_forward_pre_hook(dense,with_kwargs=True)
            try:
                with ScopeVisionSignal(vision,chunk=3) as signal:actual=vision(pixels,grid_thw=grid).pooler_output
            finally:handle.remove()
        torch.testing.assert_close(native,actual,rtol=0,atol=0)
        torch.testing.assert_close(signal.saliency,expected[0],rtol=1e-6,atol=1e-7)
        self.assertEqual(tuple(signal.features.shape),(4,32));self.assertAlmostEqual(float(signal.saliency.sum()),1,places=6)
        self.assertFalse(vision.blocks[-2].attn._forward_pre_hooks)

    def test_dart_matches_official_representable_budgets(self):
        import torch,types
        from .utils import dart_select
        oracle=self.reference('dart','Qwen2_5-VL/Qwen2_5VL_DART/modeling_qwen2_5_vl_self.py','get_retained_image_token')
        torch.manual_seed(27);hidden=torch.randn(1,83,32);keys=torch.randn(1,4,83,8)
        flattened=keys.permute(0,2,1,3).reshape(83,32);visual=torch.arange(3,67)
        for k in (4,12,20,36):
            cfg=types.SimpleNamespace(DART_config={'K':2,'image_token_start_index':3,'image_token_length':64,
                'pivot_image_token':4,'pivot_text_token':4,'reduction_ratio':1-(k-4)/64})
            expected=sorted((oracle(None,cfg,hidden,keys)-3).tolist())
            actual=dart_select(hidden[0],flattened,visual,k)
            self.assertEqual(actual['indices'],expected)

    def test_dart_exact_quota_and_input_contract(self):
        import torch
        from .utils import dart_select
        torch.manual_seed(28);h=torch.randn(41,16);keys=torch.randn(41,8)
        for k in range(1,33):
            result=dart_select(h,keys,torch.arange(3,35),k)
            self.assertEqual(len(result['indices']),k)
            self.assertEqual(len(set(result['indices'])),k)
        with self.assertRaises(ValueError):dart_select(h,keys,[3,5,8],2)

    def test_dart_chunked_large_scores_match_unchunked(self):
        import torch
        from .utils import dart_select
        torch.manual_seed(130114);hidden=torch.randn(1261,127);keys=torch.randn(1261,83)
        visual=torch.arange(3,1253);k=701
        actual=dart_select(hidden,keys,visual,k)
        image=visual[torch.norm(keys[visual],p=1,dim=-1).topk(4).indices].tolist()
        tail=torch.arange(1253,1261);text=tail[torch.norm(keys[tail],p=1,dim=-1).topk(4).indices].tolist()
        pivots=list(set(image+text));remaining=set(visual.tolist())-set(image);chosen=set(image)
        q,r=divmod(k-4,len(pivots))
        for j,pivot in enumerate(pivots):
            candidates=list(remaining);score=-torch.nn.functional.cosine_similarity(hidden[pivot],hidden[candidates],dim=-1)
            picked=[candidates[i] for i in score.topk(q+int(j<r)).indices.tolist()]
            chosen.update(picked);remaining.difference_update(picked)
        self.assertEqual(actual['indices'],sorted(i-3 for i in chosen))
        self.assertEqual(actual['image_pivots'],image);self.assertEqual(actual['text_pivots'],text)

    def test_s2prune_matches_official_all_paper_budgets(self):
        import torch
        from PIL import Image
        from .utils import s2prune_select
        oracle=self.reference('s2prune','s2prune/allocation.py')
        rng=np.random.default_rng(47);image=Image.fromarray(rng.integers(0,256,(97,113,3),dtype=np.uint8))
        scores=np.abs(rng.normal(size=576)).astype(np.float32)
        for k,g in ((32,4),(64,5),(128,8),(192,9)):
            expected=oracle.select_s2prune_tokens(torch.from_numpy(scores),image,24,24,k,g)
            actual=s2prune_select(scores,image,(24,24),k,g)
            self.assertEqual(actual['indices'],expected.selected_indices.tolist())
            self.assertEqual(actual['region_budgets'],expected.region_budgets)
            self.assertEqual(actual['final_cells'],expected.final_cells)
            np.testing.assert_array_equal(actual['raw_complexity'],expected.raw_complexity)
        with self.assertRaises(ValueError):s2prune_select(-scores,image,(24,24),32,4)

    def test_s2prune_rectangular_zero_and_extreme_shapes(self):
        from PIL import Image
        from .utils import s2prune_select
        for shape,g,k in [((5,9),2,11),((9,5),2,45),((24,24),9,192)]:
            score=np.arange(np.prod(shape),dtype=np.float32);image=Image.new('RGB',(83,57))
            actual=s2prune_select(score,image,shape,k,g)
            self.assertEqual(len(actual['indices']),k);self.assertEqual(sum(actual['region_budgets']),k)
            coverage=np.zeros(shape,dtype=int)
            for a,b,c,d in actual['final_cells']:coverage[a:b,c:d]+=1
            np.testing.assert_array_equal(coverage,np.ones(shape))

    def test_hybrid_identity_and_pruned_cached_decode(self):
        import torch
        from .utils import hybrid_prior_prefill
        model=self.tiny_model();torch.manual_seed(49);embedding=torch.randn(1,27,32)
        positions=torch.arange(27).view(1,1,-1).repeat(4,1,1);visual=torch.arange(3,19)
        with torch.no_grad():
            native=model(inputs_embeds=embedding,position_ids=positions,use_cache=True)
            for method in ('DART','S2PRUNE'):
                identity=hybrid_prior_prefill(model,embedding,positions,visual,16,method,fixed_selection=list(range(16)))
                torch.testing.assert_close(identity['hidden_states'],native.last_hidden_state,rtol=1e-5,atol=2e-6)
                fixed=[0,2,7,13,15]
                first=hybrid_prior_prefill(model,embedding,positions,visual,len(fixed),method,fixed_selection=fixed)
                boundary=2 if method=='DART' else 1
                self.assertEqual(first['trajectory'],[27]*boundary+[16]*(4-boundary))
                self.assertEqual(first['cache'].get_seq_length(),16)
                torch.testing.assert_close(first['positions'],positions[:,:,first['keep']],rtol=0,atol=0)
                full=embedding
                for step in range(2):
                    token=torch.randn(1,1,32);full=torch.cat([full,token],dim=1)
                    p=torch.full((4,1,1),27+step,dtype=torch.long);p[0]=16+step
                    actual=model(inputs_embeds=token,position_ids=p,past_key_values=first['cache'],use_cache=True).last_hidden_state
                    allpos=torch.arange(full.shape[1]).view(1,1,-1).repeat(4,1,1)
                    reference=hybrid_prior_prefill(model,full,allpos,visual,len(fixed),method,fixed_selection=fixed,use_cache=False)
                    torch.testing.assert_close(actual[:,-1],reference['hidden_states'][:,-1],rtol=2e-4,atol=2e-5)

    def test_hybrid_executes_actual_dart_and_erc_selectors(self):
        import torch
        from PIL import Image
        from .utils import hybrid_prior_prefill,dart_select,s2prune_select
        model=self.tiny_model();torch.manual_seed(59);embedding=torch.randn(1,27,32)
        positions=torch.arange(27).view(1,1,-1).repeat(4,1,1);visual=torch.arange(3,19)
        with torch.no_grad():
            dart=hybrid_prior_prefill(model,embedding,positions,visual,8,'DART')
            s2=hybrid_prior_prefill(model,embedding,positions,visual,8,'S2PRUNE',image=Image.new('RGB',(24,24)),grid=(4,4),coarse_grid=2)
        self.assertEqual(len(dart['selection']['indices']),8);self.assertEqual(len(s2['selection']['indices']),8)
        self.assertEqual(tuple(dart['signals']['keys'].shape[:2]),(1,27))
        self.assertEqual(tuple(s2['signals']['erc'].shape),(16,))
        self.assertTrue(torch.isfinite(s2['signals']['erc']).all())
        with self.assertRaises(ValueError):hybrid_prior_prefill(model,embedding.repeat(2,1,1),positions,visual,8,'DART')


class ProtectedPriors(unittest.TestCase):
    def test_scope_constrained_greedy_independent_oracle(self):
        from .utils import scope_select
        rng=np.random.default_rng(220107)
        for n,k,anchors in [(13,8,[0,4,8]),(11,3,[1,5,8]),(13,13,[2,12])]:
            f=rng.normal(size=(n,7)).astype(np.float32);s=rng.uniform(.1,1,n)
            u=f/np.linalg.norm(f,axis=1)[:,None];sim=u@u.T
            covered=np.maximum(0,np.max(sim[anchors],axis=0));selected=list(anchors)
            while len(selected)<k:
                scores={i:float(s[i]*sum(max(float(sim[i,j]-covered[j]),0) for j in range(n))) for i in range(n) if i not in selected}
                best=min(scores,key=lambda i:(-scores[i],i));selected.append(best);covered=np.maximum(covered,sim[best])
            r=scope_select(f,s,k,protected=anchors)
            self.assertEqual(r['selection_order'],selected)
            self.assertEqual(r['indices'],sorted(selected))

    def test_s2_protected_regions_counts_and_exact_budget(self):
        from .utils import s2prune_select
        from PIL import Image
        image=Image.new('RGB',(57,81));score=np.arange(45,dtype=np.float32)
        for anchors,k in [([0,1,2,3,4,5,6,7,8,9],10),([0,2,4,6,8,10],13),(list(range(39)),42),([0,44],45)]:
            r=s2prune_select(score,image,(5,9),k,2,protected=anchors);indices=r['indices']
            self.assertTrue(set(anchors)<=set(indices));self.assertEqual(indices,sorted(set(indices)));self.assertEqual(len(indices),k)
            self.assertEqual(sum(r['region_budgets']),k)
            for region,minimum,total in zip(r['regions'],r['protected_region_counts'],r['region_budgets']):
                a,b,c,d=region;ids={y*9+x for y in range(a,b) for x in range(c,d)}
                self.assertEqual(minimum,len(ids&set(anchors)));self.assertEqual(total,len(ids&set(indices)))
            nonanchors=set(indices)-set(anchors)
            for a,b,c,d in r['final_cells']:
                free={y*9+x for y in range(a,b) for x in range(c,d)}-set(anchors)
                self.assertEqual(free&nonanchors,{max(free)})  # Increasing ERC, independent cell winner.

    def test_protection_rejects_bad_contract(self):
        from .utils import protected_visual_indices
        for values in ([0,0],[True],[1.5],[-1],[8],[0,1,2]):
            with self.assertRaises(ValueError):protected_visual_indices(values,8,2)
        self.assertEqual(protected_visual_indices([5,1],8,2),[1,5])

    def test_s2_anchor_cache_continuation_matches_recomputation(self):
        import torch
        from PIL import Image
        from .utils import hybrid_prior_prefill
        model=PriorCompletion.tiny_model();torch.manual_seed(22108);embedding=torch.randn(1,27,32)
        positions=torch.arange(27).view(1,1,-1).repeat(4,1,1);visual=torch.arange(3,19);anchors=[0,7,15]
        with torch.no_grad():
            first=hybrid_prior_prefill(model,embedding,positions,visual,8,'S2PRUNE',image=Image.new('RGB',(24,24)),grid=(4,4),coarse_grid=2,protected=anchors)
            selected=first['selection']['indices'];self.assertTrue(set(anchors)<=set(selected))
            self.assertEqual(first['trajectory'],[27,19,19,19]);full=embedding
            for step in range(2):
                token=torch.randn(1,1,32);full=torch.cat([full,token],dim=1)
                p=torch.full((4,1,1),27+step,dtype=torch.long);p[0]=19+step
                actual=model(inputs_embeds=token,position_ids=p,past_key_values=first['cache'],use_cache=True).last_hidden_state
                allpos=torch.arange(full.shape[1]).view(1,1,-1).repeat(4,1,1)
                expected=hybrid_prior_prefill(model,full,allpos,visual,8,'S2PRUNE',fixed_selection=selected,protected=anchors,use_cache=False)
                torch.testing.assert_close(actual[:,-1],expected['hidden_states'][:,-1],rtol=2e-4,atol=2e-5)


class Integrity(unittest.TestCase):
    def test_gather_keeps_native_coordinates_and_all_nonpadding_text(self):
        from .utils import visual_gather_plan
        ids=np.array([0,10,99,99,99,99,11,12]);mask=np.array([0,1,1,1,1,1,1,1])
        positions=np.array([[0,0,1,1,1,1,3,4],[0,0,1,1,2,2,3,4],[0,0,1,2,1,2,3,4]])
        full=visual_gather_plan(ids,positions,mask,99,[0,1,2,3])
        np.testing.assert_array_equal(full['retained_input_indices'],np.arange(1,8))
        pruned=visual_gather_plan(ids,positions,mask,99,[0,3])
        np.testing.assert_array_equal(pruned['retained_input_indices'],[1,2,5,6,7])
        np.testing.assert_array_equal(pruned['retained_position_ids'],positions[:,[1,2,5,6,7]])
        self.assertEqual(pruned['text_tokens'],3);self.assertEqual(pruned['next_text_position'],full['next_text_position'])
        self.assertEqual(pruned['rope_delta_after_gather']+pruned['input_tokens'],5)
        for bad in ([0,0],[3,0],[-1],[4],[True]):
            with self.assertRaises(ValueError):visual_gather_plan(ids,positions,mask,99,bad)

    def test_source_semantics_on_all_three_fixed_cases(self):
        from .gates import audit_source_projection
        for oid in ('INC-540349CB2170','INC-5D92F3402F88','INC-1EF3346D26B2'):
            p=read_json(SOURCE/(oid+'.json'));c=compile_case(p);v=comparison_provenance(c,p)
            self.assertEqual(audit_source_projection(p,c,v)['issues'],[],oid)
    def test_independent_source_audit_detects_changes(self):
        from copy import deepcopy
        from .gates import audit_source_projection
        public=read_json(SOURCE/'INC-6E627662CA32.json');compiled=compile_case(public)
        prov=comparison_provenance(compiled,public)
        self.assertEqual(audit_source_projection(public,compiled,prov)['issues'],[])
        for kind in ('metric','trace','log','graph','inventory'):
            bad=deepcopy(compiled)
            c=next(c for c in bad['evidence']['cards'] if c['kind']==kind)
            if kind=='metric':c['data']['values'][0]=123456789
            elif kind=='trace':c['unit']='ms'
            elif kind=='log':c['data']['counts'][0]+=1
            elif kind=='graph':c['data']['edges'][0]['source']='wrong'
            else:c['data']['identities'].reverse()
            self.assertEqual(audit_source_projection(public,bad,prov)['status'],'failed',kind)

    def test_caption_roles_are_typed_and_metadata_is_context(self):
        from .exps import detail_label
        public=read_json(SOURCE/'INC-6E627662CA32.json');compiled=compile_case(public)
        prov=comparison_provenance(compiled,public)
        self.assertEqual(prov['foreground']['schema'],'CanonicalForegroundV2')
        for role in prov['roles']:
            self.assertNotIn('rank_score',role['source_occurrence'])
            self.assertNotIn('signed_z',role['source_occurrence'])
            self.assertFalse(role['source_occurrence'].endswith('/score'))
        rates=[r for r in prov['roles'] if r['quantity'] in {'error_rate','log_rate'}]
        self.assertTrue(rates)
        self.assertTrue(all(r['unit']=='events/min' and r['phase'] in {'reference','current'} for r in rates))
        r=public['payload']['relations'][0]
        label=detail_label('/'+r['id']+'/phases/current/quantiles/1/1',1,{},public)
        self.assertIn('current · child p95 · ms',label)
        label=detail_label('/'+r['id']+'/phases/reference/binary/2',1,{},public)
        self.assertIn('parent>p95 child≤p95 · count',label)

    def test_phase_is_source_bin_center_and_text_keeps_all_records(self):
        from .exps import text_conditions
        from .gates import audit_source_projection
        p=read_json(SOURCE/'INC-DD972245679A.json');c=compile_case(p);v=comparison_provenance(c,p)
        self.assertEqual(audit_source_projection(p,c,v)['status'],'passed')
        boundary=[r for r in v['roles'] if r['quantity']=='recorded_series' and any(t['binding'].endswith('.sample.42') for t in r['targets'])]
        self.assertTrue(boundary);self.assertTrue(all(r['phase']=='reference' for r in boundary))
        text=text_conditions(p,c,v)
        self.assertEqual(text['T_FULL'],p['texts']['RAW_TEXT']);self.assertEqual(text['T_FULL'],text['T_NATIVE'])
        for arm in ('T_LEDGER','T_DEP'):
            decoded=[json.loads(line) for line in text[arm][0]['text'].splitlines() if line.startswith('{"source":')]
            self.assertEqual(sorted(decoded,key=lambda x:x['source']),sorted(c['ledger']['records'],key=lambda x:x['source']))
        boundary[0]['phase']='current'
        self.assertIn('Metric bin-center phase differs',audit_source_projection(p,c,v)['issues'])

    def test_codec_lossless_and_rejects_overlap(self):
        self.assertEqual(decode_sequence({'length':5,'value_positions':[[0,'0,4'],[None,'1-2'],[-7,'3']]}),[0,None,None,-7,0])
        for code in ({'length':2,'value_positions':[[0,'0']]}, {'length':1,'value_positions':[[1,'0'],[2,'0']]}):
            with self.assertRaises(ValueError):decode_sequence(code)

    def test_atomic_json(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'record.json';save_json(p,{'status':'committed'})
            self.assertEqual(read_json(p),{'status':'committed'})
            with self.assertRaises(ValueError):save_json(p,{'not_finite':float('nan')})
            self.assertEqual(read_json(p),{'status':'committed'})

    def test_unknown_source_fails(self):
        p=read_json(SOURCE/'INC-6E627662CA32.json')
        p['organization']['atoms'].append({'kind':'literal','id':'xx','raw':'Unknown diagnostic observation: value 8'})
        with self.assertRaises(ValueError):ledger(p)

    def test_ignored_qa_is_isolated_and_unknown_metadata_rejected(self):
        p=read_json(SOURCE/'INC-6E627662CA32.json');before=stable_hash(compile_case(p))
        p['qa']={'historic_answer':'must not enter the source compiler'}
        self.assertEqual(stable_hash(compile_case(p)),before)
        atom=next(a for a in p['organization']['atoms'] if a.get('prefix')=='propagation_service')
        v=json.loads(atom['value_wire']);v['unknown_private_field']='not public';atom['value_wire']=json.dumps(v)
        with self.assertRaisesRegex(ValueError,'Unknown observed-onset metadata'):compile_case(p)

    def test_text_static_no_incident(self):
        self.assertNotIn('INC-',VISUAL_TASK)
        self.assertNotIn('exact values are in the text',VISUAL_TASK)
        self.assertIn('exactly five distinct',VISUAL_TASK)

    def test_complete_source_not_claimed_from_dto(self):
        p=compile_case(read_json(SOURCE/'INC-6E627662CA32.json'))
        self.assertFalse(p['source_complete_claim'])
        self.assertTrue(any(c['kind']=='metric' for c in p['evidence']['cards']))
        self.assertTrue(any(c['kind']=='graph' for c in p['evidence']['cards']))
        self.assertFalse(any(c['kind']=='literal' for c in p['evidence']['cards']))
        candidate=next(c for c in p['evidence']['cards'] if c['title'].startswith('Candidate IDs'))
        self.assertEqual(candidate['data']['identities'],read_json(SOURCE/'INC-6E627662CA32.json')['candidates'])

    def test_canonical_roles_do_not_double_weight_scalar_caption(self):
        public=read_json(SOURCE/'INC-6E627662CA32.json');p=compile_case(public)
        prov=comparison_provenance(p,public);aliases=prov['noncanonical_presentations']
        self.assertTrue(any(a['path']=='/exl_p95_base_us' for a in aliases))
        target_bindings={t['binding'] for r in prov['roles'] for t in r['targets']}
        self.assertFalse(any(a['binding'] in target_bindings for a in aliases))
        distinct=[r for r in prov['roles'] if r['quantity']=='recorded_series']
        self.assertEqual(len(distinct),len({(r['source_occurrence'],r['phase']) for r in distinct}))

    def test_canvas_cap_and_historical_default(self):
        from renderer.utils import compile_design
        p=compile_case(read_json(SOURCE/'INC-6E627662CA32.json'))
        self.assertLessEqual(p['design']['viewport']['width'],8192)
        self.assertLessEqual(p['design']['viewport']['height'],8192)
        for field in ('width','height'):
            changed=json.loads(json.dumps(p['design']));changed['viewport'][field]=8193
            with self.assertRaises(ValueError):compile_design(p['evidence'],changed)
        changed=json.loads(json.dumps(p['design']));del changed['canvas_extent']
        with self.assertRaises(ValueError):compile_design(p['evidence'],changed)


class Foreground(unittest.TestCase):
    def test_actual_ink_collision_not_rectangular_support(self):
        # Synthetic audit rasters, not diagnostic dashboards/model inputs.
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);a=np.zeros((64,64,4),dtype=np.uint8)
            a[2:4,2:4]=[64,64,76,255];a[8:16,8:16]=[64,64,88,255]
            Image.fromarray(a).save(p/'role_foreground.png')
            b=np.zeros_like(a);b[40:42,40:42]=255
            Image.fromarray(b).save(p/'anchor_foreground.png')
            save_json(p/'foreground_audit.json',{'issues':[],'palette':{'a':[64,64,76],'b':[64,64,88]},
                'boxes':{'a':[[0,0,64,64]],'b':[[0,0,64,64]]}})
            s=foreground_support(p,[64,64])
            self.assertEqual(s['anchors'],[3]);self.assertEqual(s['definite_empty_unanchored_roles'],['a'])
            self.assertEqual(s['roles']['a']['foreground_possible_tokens'],[0])
            self.assertEqual(s['roles']['b']['tokens'],[0])
            self.assertEqual(s['foreground_union_tokens'],2)
            shared=foreground_support(p,[64,64],policy='shared_v2')
            self.assertEqual(shared['roles']['a']['tokens'],[0])
            self.assertEqual(shared['roles']['b']['tokens'],[0])
            self.assertFalse(shared['definite_empty_unanchored_roles'])
            self.assertFalse(shared['uncertain_empty_unanchored_roles'])
            self.assertEqual(shared['shared_nonanchor_tokens'],1)
            self.assertEqual(shared['role_token_incidences'],2)
            self.assertEqual(shared['foreground_union_tokens'],2)

    def test_fully_anchored_is_not_a_mapping_failure(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);a=np.zeros((32,64,4),dtype=np.uint8)
            a[2:4,2:4]=[64,64,76,255]
            Image.fromarray(a).save(p/'role_foreground.png');Image.fromarray(a).save(p/'anchor_foreground.png')
            save_json(p/'foreground_audit.json',{'issues':[],'palette':{'a':[64,64,76]},'boxes':{'a':[[2,2,2,2]]}})
            s=foreground_support(p,[64,32])
            self.assertTrue(s['roles']['a']['fully_anchored']);self.assertFalse(s['definite_empty_unanchored_roles'])


class Attention(unittest.TestCase):
    def test_record_and_peak_budget(self):
        self.assertLessEqual(AttentionStore.storage_ceiling(),1_000_000_000)
        with tempfile.TemporaryDirectory() as d:
            store=AttentionStore(d)
            record={'schema':'AttentionSummaryV1','status':'measured','layer':3,
                    'normalization':'all_visible_keys','text_mass':.2,'image_mass':.7,'other_mass':.1,
                    'text_regions':[.1,.1],'image_regions':[.2,.5],'image_grid':[[0]*32 for _ in range(32)],
                    'sample_count':1,'query_definition':'last_prompt_query','mapping_hash':'0'*64}
            self.assertTrue(store.submit(stable_hash('call1'),record));store.close()
            p=next(Path(d).glob('*.json'));self.assertLessEqual(p.stat().st_size,65536)
            self.assertEqual(json.loads(p.read_text()),record)

    def test_reject_raw_tensor_or_oversized_record(self):
        with tempfile.TemporaryDirectory() as d:
            store=AttentionStore(d)
            for value in ({'schema':'AttentionSummaryV1','query_states':[1]},
                          {'schema':'AttentionSummaryV1','image_grid':[1]*70000}):
                with self.assertRaises(ValueError):store.submit(stable_hash('bad'),value)
            store.close()


class Selector(unittest.TestCase):
    def test_diversity_domain_optimization_equals_dense_reference(self):
        for seed in range(6):
            rng=np.random.default_rng(seed);features=rng.normal(size=(30,32)).astype(np.float32)
            xy=np.array([[i%6,i//6] for i in range(30)],np.float32)
            roles={'a':{'tokens':[4,5,6,9,11],'bbox_diag2':20.,'patch_diag2':2.},
                   'b':{'tokens':[5,8,12,14,18],'bbox_diag2':20.,'patch_diag2':2.}}
            edges=[{'type':'pair','roles':['a','b']}]
            a=select_tokens(features,xy,roles,[0,1,2],edges,mode='DIVERSITY',budget_policy='optional_support_v3',engine='incremental_v3')
            b=select_tokens(features,xy,roles,[0,1,2],edges,mode='DIVERSITY',budget_policy='optional_support_v3',engine='exhaustive_v2')
            self.assertEqual(a['indices'],b['indices']);self.assertEqual(a['quality'],b['quality'])

    def setUp(self):
        self.f=np.array([[1,0],[0,1],[1,1],[-1,1],[1,-1],[2,1]],float)
        self.xy=np.array([[i%3,i//3] for i in range(6)],float)
        self.roles={f'u{i}':{'tokens':[2*i,2*i+1],'bbox_diag2':2.,'patch_diag2':2.} for i in range(3)}
        self.edges=[{'type':'pair','roles':['u0','u1']},{'type':'pair','roles':['u1','u2']}]

    def brute_quality(self,selected):
        norm=self.f/np.linalg.norm(self.f,axis=1)[:,None];q={}
        for u,r in self.roles.items():
            values=[]
            for i in r['tokens']:
                sim=[]
                for j in r['tokens']:
                    if j in selected:
                        dist=.5*(1-float(norm[i]@norm[j]))/2+.5*min(1,float(((self.xy[i]-self.xy[j])**2).sum())/2)
                        sim.append(1-dist)
                values.append(max(sim,default=0))
            q[u]=sum(values)/len(values)
        return q

    def test_exact_budget_determinism_objective_and_optimum_bound(self):
        for mode in ('CVC','UNARY','UNIFORM','DIVERSITY'):
            result=select_tokens(self.f,self.xy,self.roles,[],self.edges,.5,mode)
            other=select_tokens(self.f,self.xy,self.roles,[],self.edges,.5,mode)
            self.assertEqual(result['indices'],other['indices']);self.assertEqual(len(result['indices']),3)
            q=self.brute_quality(set(result['indices']))
            self.assertAlmostEqual(result['objective'],objective(q,self.edges),places=6)
            optimum=max(objective(self.brute_quality(set(s)),self.edges) for s in itertools.combinations(range(6),3))
            self.assertLessEqual(result['objective'],optimum+1e-6)

    def test_independent_retained_quality_detects_mutation(self):
        from .utils import audit_selected_quality
        result=select_tokens(self.f,self.xy,self.roles,[],self.edges,.5)
        self.assertEqual(audit_selected_quality(self.f,self.xy,self.roles,result['indices'],result['quality'])['status'],'passed')
        wrong=dict(result['quality']);wrong['u0']+=.1
        with self.assertRaises(ValueError):audit_selected_quality(self.f,self.xy,self.roles,result['indices'],wrong)

    def test_anchors_and_empty_support(self):
        roles={k:dict(v) for k,v in self.roles.items()};roles['u0']={'tokens':[],'fully_anchored':True}
        result=select_tokens(self.f,self.xy,roles,[0,1],self.edges,.5)
        self.assertTrue({0,1}<=set(result['indices']));self.assertEqual(result['quality']['u0'],1)
        roles['u0']['fully_anchored']=False
        with self.assertRaises(ValueError):select_tokens(self.f,self.xy,roles,[0,1],self.edges,.5)
        with self.assertRaises(ValueError):select_tokens(self.f,self.xy,self.roles,[0,1,2,3],self.edges,.5)

    def test_unary_weights_degree_preservation(self):
        original=[{'type':'a','roles':['a','b']},{'type':'a','roles':['c','d']}]
        rewired=[{'type':'a','roles':['a','d']},{'type':'a','roles':['c','b']}]
        self.assertEqual(coefficients(original),coefficients(rewired))
        q={'a':1,'b':1,'c':0,'d':0}
        self.assertEqual(objective(q,original,True),objective(q,rewired,True))
        self.assertNotEqual(objective(q,original),objective(q,rewired))

    def test_zero_features_have_self_similarity_one(self):
        z=np.zeros_like(self.f)
        result=select_tokens(z,self.xy,self.roles,[],self.edges,1.)
        self.assertEqual(result['indices'],list(range(6)))
        self.assertEqual(result['quality'],{k:1. for k in self.roles})


class SharedSelector(unittest.TestCase):
    def quality(self,features,xy,roles,selected):
        # Independent scalar implementation of the mathematical proxy.
        f=np.asarray(features,float);length=np.linalg.norm(f,axis=1)
        f=f/np.where(length==0,1,length)[:,None];out={}
        for u,r in roles.items():
            ids=set(r['tokens'])
            if not ids:
                if not r.get('fully_anchored'):raise ValueError('Empty role')
                out[u]=1.;continue
            scores=[]
            for i in ids:
                options=[]
                for j in ids&set(selected):
                    if i==j:options.append(1.);continue
                    cosine=np.clip(sum(f[i]*f[j]),-1,1)
                    distance=sum((np.asarray(xy[i])-np.asarray(xy[j]))**2)
                    options.append(1-.25*(1-cosine)-.5*min(1,distance/max(r['bbox_diag2'],r['patch_diag2'])))
                scores.append(max(options,default=0.))
            out[u]=sum(scores)/len(scores)
        return out

    def role(self,tokens):return {'tokens':tokens,'bbox_diag2':4.,'patch_diag2':2.}

    def test_shared_token_updates_both_operands_at_cost_one(self):
        f=np.eye(4);xy=np.array([[i,0] for i in range(4)],float)
        roles={'a':self.role([0]),'b':self.role([0]),'c':self.role([1]),'d':self.role([2])}
        edges=[{'type':'pair','roles':['a','b']},{'type':'pair','roles':['c','d']}]
        result=select_tokens(f,xy,roles,[],edges,.25,trace=True)
        self.assertEqual(result['indices'],[0]);self.assertEqual(result['unique_token_cost'],1)
        self.assertEqual(result['optional_incidences_covered'],2)
        self.assertEqual(result['quality']['a'],1.);self.assertEqual(result['quality']['b'],1.)
        self.assertEqual(result['actions'][0]['affected_roles'],['a','b'])

    def test_joint_union_gain_is_not_sum_of_single_gains(self):
        f=np.eye(4);xy=np.array([[i,0] for i in range(4)],float)
        roles={'a':self.role([0,1,2]),'b':self.role([0]),'c':self.role([1])}
        edges=[{'type':'pair','roles':['b','c']},{'type':'singleton','roles':['a']}]
        result=select_tokens(f,xy,roles,[],edges,.5,trace=True)
        self.assertEqual(result['actions'][0]['tokens'],[0,1]);self.assertEqual(result['actions'][0]['cost'],2)
        independent=self.quality(f,xy,roles,{0,1})
        self.assertAlmostEqual(result['quality']['a'],independent['a'],places=6)
        self.assertAlmostEqual(result['actions'][0]['gain'],objective(independent,edges),places=6)
        additive=self.quality(f,xy,roles,{0})['a']+self.quality(f,xy,roles,{1})['a']
        self.assertGreater(additive,independent['a'])

    def test_overlapping_actions_match_independent_quality_and_optimum_bound(self):
        rng=np.random.default_rng(32)
        for _ in range(12):
            f=rng.normal(size=(7,4));xy=np.array([[i%4,i//4] for i in range(7)],float)
            roles={u:self.role(sorted(rng.choice(6,size=3,replace=False).tolist())) for u in 'abcd'}
            edges=[{'type':'pair','roles':['a','b']},{'type':'pair','roles':['c','d']}]
            for mode in ('CVC','REWIRED','UNARY','QUOTA','UNIFORM','DIVERSITY'):
                result=select_tokens(f,xy,roles,[6],edges,4/7,mode,trace=True)
                self.assertEqual(len(result['indices']),4);self.assertEqual(len(set(result['indices'])),4)
                q=self.quality(f,xy,roles,result['indices'])
                for u in roles:self.assertAlmostEqual(q[u],result['quality'][u],places=6)
                optimum=max(objective(self.quality(f,xy,roles,set(s)|{6}),edges) for s in itertools.combinations(range(6),3))
                self.assertLessEqual(result['objective'],optimum+1e-6)
                changed={u:{**r,'tokens':r['tokens']+r['tokens'][:1]} for u,r in reversed(list(roles.items()))}
                repeat=select_tokens(f,xy,changed,[6],list(reversed(edges)),4/7,mode)
                self.assertEqual(result['indices'],repeat['indices'])

    def test_quota_redistributes_shared_credit_without_extra_tokens(self):
        self.assertEqual(quota_targets({'b':1,'a':1,'c':4},4),{'a':1,'b':1,'c':2})
        self.assertEqual(sum(quota_targets({'a':1,'b':3},8).values()),4)
        f=np.eye(6);xy=np.array([[i,0] for i in range(6)],float)
        roles={'a':self.role([0,1]),'b':self.role([0,1])};edges=[{'type':'pair','roles':['a','b']}]
        r=select_tokens(f,xy,roles,[],edges,.5,'QUOTA',trace=True)
        self.assertEqual(len(r['indices']),3);self.assertTrue({0,1}<=set(r['indices']))
        self.assertEqual(r['quality'],{'a':1.,'b':1.})
        self.assertEqual(sum(a['cost'] for a in r['actions']),3)

    def test_saturation_certificate_is_not_claimed_as_measured_masks(self):
        roles={'a':self.role([0,1]),'b':self.role([1,2])}
        s=support_saturation(roles,[3],8,.5)
        self.assertTrue(s['all_support_fits']);self.assertEqual(s['unique_support_union'],4)
        self.assertFalse(s['actual_heuristic_masks_measured'])
        self.assertFalse(support_saturation(roles,[3],8,.25)['all_support_fits'])

    def test_degree_matched_dependencies_can_change_shared_allocation(self):
        rng=np.random.default_rng(781);f=rng.normal(size=(8,4));xy=np.array([[i%4,i//4] for i in range(8)],float)
        roles={u:{'tokens':sorted(rng.choice(8,3,replace=False).tolist()),'bbox_diag2':10.,'patch_diag2':2.} for u in 'abcd'}
        true=[{'type':'pair','roles':['a','b']},{'type':'pair','roles':['c','d']}]
        rewired=[{'type':'pair','roles':['a','d']},{'type':'pair','roles':['c','b']}]
        self.assertEqual(coefficients(true),coefficients(rewired))
        a=select_tokens(f,xy,roles,[],true,.25);b=select_tokens(f,xy,roles,[],rewired,.25,'REWIRED')
        self.assertNotEqual(a['indices'],b['indices'])
        ua=select_tokens(f,xy,roles,[],true,.25,'UNARY');ub=select_tokens(f,xy,roles,[],rewired,.25,'UNARY')
        self.assertEqual(ua['indices'],ub['indices'])
        for edges,result in [(true,a),(rewired,b)]:
            optimum=max(objective(self.quality(f,xy,roles,s),edges) for s in itertools.combinations(range(8),2))
            self.assertLessEqual(result['objective'],optimum+1e-6)

    def test_incremental_search_equals_exhaustive_under_both_budgets(self):
        rng=np.random.default_rng(9041)
        for trial in range(24):
            f=rng.normal(size=(12,6));xy=np.array([[i%4,i//4] for i in range(12)],float)
            roles={u:self.role(sorted(rng.choice(10,4,replace=False).tolist())) for u in 'abcdef'}
            edges=[{'type':'pair','roles':['a','b']},{'type':'pair','roles':['b','c']},
                   {'type':'pair','roles':['d','e']},{'type':'single','roles':['f']}]
            for policy in ('grid_v2','optional_support_v3'):
                for mode in ('CVC','REWIRED','UNARY'):
                    opts=dict(fraction=.5,mode=mode,budget_policy=policy,trace=True)
                    a=select_tokens(f,xy,roles,[10],edges,engine='exhaustive_v2',**opts)
                    b=select_tokens(f,xy,roles,[10],edges,engine='incremental_v3',**opts)
                    self.assertEqual(a['indices'],b['indices']);self.assertEqual(a['quality'],b['quality'])
                    self.assertEqual(a['actions'],b['actions'])

    def test_evidence_budget_is_not_grid_retention_and_all_controls_match(self):
        f=np.eye(12);xy=np.array([[i,0] for i in range(12)],float)
        roles={'a':self.role([1,2,3]),'b':self.role([3,4])};edges=[{'type':'pair','roles':['a','b']}]
        plan=evidence_budget(roles,[0],12,.5,'optional_support_v3')
        self.assertEqual(plan['total_tokens'],3);self.assertEqual(plan['actual_grid_fraction'],.25)
        self.assertFalse(plan['all_support_fits'])
        for mode in ('CVC','REWIRED','UNARY','QUOTA','UNIFORM','DIVERSITY'):
            r=select_tokens(f,xy,roles,[0],edges,.5,mode,budget_policy='optional_support_v3')
            self.assertEqual(len(r['indices']),3);self.assertIn(0,r['indices'])
            self.assertTrue(set(r['indices'])<=set(range(5)))
        empty={'a':{'tokens':[],'fully_anchored':True}}
        r=select_tokens(f,xy,empty,[0],[{'type':'single','roles':['a']}],.5,budget_policy='optional_support_v3')
        self.assertEqual(r['indices'],[0]);self.assertTrue(r['budget']['all_support_fits'])
        config={'budget_policy':'optional_support_v3','conditions':['CVC_E50','DART_E50']}
        actual=select_registered_condition(config,'CVC_E50',f,xy,roles,[0],edges)
        self.assertEqual(actual['budget']['total_tokens'],3)
        for bad in ('CVC50','DART_E50'):
            with self.assertRaises(ValueError):select_registered_condition(config,bad,f,xy,roles,[0],edges)
        with self.assertRaises(ValueError):select_registered_condition(config,'CVC_E50',f,xy,roles,[0],edges,budget_policy='grid_v2')

    def test_covariate_matched_rewire_preserves_every_degree_and_no_true_edges(self):
        edges=[{'type':'pair','roles':[a,b]} for a,b in [('a','b'),('c','d'),('e','f')]]
        cov={u:{'area':.1,'dispersion':.2,'center':[0.,0.],
                'signature':['duration','ms','reference' if u in 'ace' else 'current']} for u in 'abcdef'}
        bins=fit_rewire_bins([{'edges':edges,'covariates':cov,'diagonal':1}])
        a,report=matched_rewire(edges,cov,bins,1,93);b,repeat=matched_rewire(edges,cov,bins,1,93)
        from .utils import audit_rewired_graph
        self.assertEqual(audit_rewired_graph(edges,a,cov,bins,1)['status'],'passed')
        wrong=[{'type':e['type'],'roles':list(e['roles'])} for e in a];wrong[0]['roles'][0]=wrong[0]['roles'][1]
        with self.assertRaises(ValueError):audit_rewired_graph(edges,wrong,cov,bins,1)
        self.assertEqual(a,b);self.assertEqual(report,repeat);self.assertTrue(report['graph_changed'])
        self.assertEqual(report['types']['pair']['proposals'],300)
        def degrees(es):
            from collections import Counter
            return Counter((e['type'],u) for e in es for u in e['roles'])
        self.assertEqual(degrees(edges),degrees(a));self.assertEqual(coefficients(edges),coefficients(a))
        original={tuple(e['roles']) for e in edges}
        for e in a:
            if tuple(e['roles']) not in original:
                self.assertEqual(len(set(e['roles'])),2)
                self.assertEqual(cov[e['roles'][0]]['signature'][-1],'reference')
                self.assertEqual(cov[e['roles'][1]]['signature'][-1],'current')
        for u in cov:cov[u]['signature'][1]=u
        same,blocked=matched_rewire(edges,cov,bins,1,93)
        self.assertFalse(blocked['graph_changed']);self.assertEqual(same,edges)


@unittest.skipUnless(importlib.util.find_spec('torch'),'Torch-specific CPU regression uses infer environment')
class PassiveAttention(unittest.TestCase):
    def test_gqa_reduction_and_bounded_eos_buffer(self):
        import torch
        from types import SimpleNamespace
        from .utils import attention_region_summary,PassiveAttentionTap
        torch.set_num_threads(1);torch.manual_seed(710)
        q=torch.randn(1,4,5,8);k=torch.randn(1,2,5,8)
        region=torch.tensor([0,1,1,2,2],dtype=torch.long)
        mask=torch.tensor([[[[True,True,True,True,False]]]])
        actual=attention_region_summary(q,k,region,3,8**-.5,mask)
        expanded=k.repeat_interleave(2,dim=1)
        score=(q[:,:,-1:,:]*expanded).sum(-1)*8**-.5
        weight=score.masked_fill(~mask[0],-torch.inf).softmax(-1).mean(1)[0]
        expected=torch.stack([weight[region==i].sum() for i in range(3)])
        torch.testing.assert_close(actual,expected,rtol=1e-6,atol=1e-7)
        with tempfile.TemporaryDirectory() as d:
            store=AttentionStore(d);tap=PassiveAttentionTap(store)
            for i in range(12):
                tap.begin(stable_hash(['eos',i]),region,['other:special','text:instructions','image:dashboard'],stable_hash('map'))
                tap.observe(SimpleNamespace(layer_idx=3),q,k,mask,8**-.5);tap.end()
                tap.pending.join();store.queue.join()
                self.assertLessEqual(len(tap.samples),1)
            tap.close();store.close()
            self.assertEqual(len(list(Path(d).glob('*.json'))),12)
            for p in Path(d).glob('*.json'):
                r=read_json(p);self.assertEqual(r['sample_count'],1)
                self.assertGreater(r['text_mass'],0);self.assertGreater(r['image_mass'],0)
                self.assertLessEqual(p.stat().st_size,65536)




class RemainingCPU(unittest.TestCase):
    def test_local_scorer_without_external_repository_or_legacy_default(self):
        """A clean process blocks the old route, even when inherited env is stale."""
        import subprocess,sys,os
        script='''
import json,sys
sys.modules['vlmrca.upstream']=None
sys.modules['vlmrca.eval.scoring']=None
sys.modules['unified_scripts.rca_scorer']=None
sys.modules['RQs.RQ2_1.src.utils']=None
from unittest.mock import patch
from scorer import RCAScorer,RCAScorerConfig,score_bound_response
from RQs.RQ4_1.src.utils import local_rca_scorer,rca_schema
assert RCAScorer(RCAScorerConfig.load()).score(['checkoutservice-2'],['checkoutservice']).mrr==1.
with patch.object(RCAScorer,'_default_hit',side_effect=AssertionError('legacy default used')):
    scorer=local_rca_scorer()
    assert scorer.hit.__module__=='scorer.matching'
    examples=[(' CheckoutService_CPU ','checkoutservice',True),
              ('checkoutservice-2','checkoutservice',True),
              ('checkoutservice-cbf9bf77c-knq2c','checkoutservice',True),
              ('checkoutservice-2','checkoutservice-1',False),
              ('node-2','node-1',False)]
    for predicted,accepted,expected in examples:assert scorer.hit(predicted,accepted)==expected
    metrics=scorer.score(['other','checkoutservice-2'],['checkoutservice']).as_dict()
    assert metrics['mrr']==.5 and metrics['ac@1']==0 and metrics['ac@3']==1
    ids=['101','102','103','104','105'];mapping=dict(zip(ids,['other','checkoutservice-2','a','b','c']))
    response=json.dumps({'services':ids,'reason':'fixture','confidence':'low'})
    assert score_bound_response(response,ids,mapping,['checkoutservice'],rca_schema(),scorer)['metrics']['mrr']==.5
    bad=json.dumps({'services':['999',*ids[1:]],'reason':'fixture','confidence':'low'})
    assert score_bound_response(bad,ids,mapping,['checkoutservice'],rca_schema(),scorer)['metrics']['mrr']==0
assert sys.modules['vlmrca.upstream'] is None
'''
        for external in (None,'/nonexistent/blocked_external_RCA_checkout'):
            env=dict(os.environ);env.pop('RL_SLM_RCA_ROOT',None)
            if external is not None:env['RL_SLM_RCA_ROOT']=external
            result=subprocess.run([sys.executable,'-B','-c',script],env=env,text=True,capture_output=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    def test_generate_adapter_restores_request_state_after_failure(self):
        if importlib.util.find_spec('torch') is None:self.skipTest('torch required')
        import torch
        from types import SimpleNamespace
        from .utils import injected_generate
        class Model:
            def __init__(self):
                self.config=SimpleNamespace(image_token_id=99)
                self.model=SimpleNamespace(rope_deltas='original',get_rope_index=lambda ids,**kw:(torch.stack([torch.arange(ids.shape[1]).repeat(len(ids),1)]*3),None))
                self.failure=False
            def get_input_embeddings(self):return lambda ids:ids[...,None].repeat(1,1,3).float()
            def _prepare_position_ids_for_generation(self,*args):return 'native'
            def generate(self,**kw):
                if self.failure:raise RuntimeError('simulated generation interruption')
                self.seen=kw
                self.assert_fresh=kw['use_cache'] and 'past_key_values' not in kw
                return kw['inputs_embeds'].clone()
        model=Model();ids=torch.tensor([[1,99,99,2]])
        batch={'input_ids':ids,'attention_mask':torch.ones_like(ids),'image_grid_thw':torch.tensor([[1,2,4]]),'mm_token_type_ids':(ids==99).long()}
        features=[torch.arange(6).reshape(2,3).float()]
        out=injected_generate(model,batch,features,[[0,1]],{'max_new_tokens':16})
        self.assertEqual(out.shape,(1,4,3));self.assertTrue(model.assert_fresh)
        self.assertEqual(model.model.rope_deltas,'original');self.assertNotIn('_prepare_position_ids_for_generation',model.__dict__)
        model.failure=True
        with self.assertRaises(RuntimeError):injected_generate(model,batch,features,[[0]],{'max_new_tokens':16})
        self.assertEqual(model.model.rope_deltas,'original');self.assertFalse(model._rq41_request_lock.locked())
        model.failure=False
        self.assertEqual(injected_generate(model,batch,features,[[1]],{'max_new_tokens':16}).shape,(1,3,3))
        with self.assertRaises(ValueError):injected_generate(model,batch,features,[[1]],{'max_new_tokens':16,'past_key_values':object()})
    def test_attention_dom_mapping_text_image_and_retention(self):
        from .utils import attention_key_regions
        manifest={'source_png':{'width':100,'height':100},'audit':{'header':{'x':0,'y':0,'width':100,'height':25},
            'bindings':[{'key':'G.edge.1','x':0,'y':25,'width':50,'height':25},
                        {'key':'M.entity','x':50,'y':50,'width':50,'height':25}]}}
        ids=np.array([1]+[99]*16+[2]);a=attention_key_regions(manifest,(4,4),ids,99)
        self.assertEqual(a['key_region'][0],0);self.assertEqual(a['key_region'][-1],0)
        self.assertTrue(all(a['key_region'][1:5]==a['regions'].index('image:title')))
        selected=[0,5,10,15];b=attention_key_regions(manifest,(4,4),ids,99,selected)
        np.testing.assert_array_equal(b['key_region'],a['key_region'][[0]+[x+1 for x in selected]+[17]])
        self.assertIn(a['regions'].index('image:relations'),a['key_region'])
    def test_qa_joint_scoring_and_anonymous_metadata(self):
        from . import exps
        public=read_json(SOURCE/'INC-6E627662CA32.json');c=compile_case(public);v=comparison_provenance(c,public)
        p=exps.qa_packet(public,c,v,'INC-6E627662CA32')
        self.assertGreater(p['applicable_blocks'],0)
        answer=[]
        for b in p['blocks']:
            answer.append({'read':{'value_A':b['A']['value'],'value_B':b['B']['value']},
                'bind':{k:b[k]['binding_answer'] for k in ('A','B')},'compare':b['comparison']})
        answer += [None]*(2-len(answer))
        self.assertEqual(exps.score_linked_qa(p,json.dumps({'blocks':answer}))['joint'],1.)
        answer[0]['read']['value_A']+=10000000
        self.assertEqual(exps.score_linked_qa(p,json.dumps({'blocks':answer}))['blocks'][0]['joint'],0)
        self.assertEqual(exps.score_linked_qa(p,'broken')['joint'],0)
        for badge in p['public_badges']:self.assertEqual(set(badge),{'slot','badge','binding','part'})
        self.assertNotIn('INC-',exps.QA_TASK)
        self.assertEqual(p['design']['qa_badges'],exps.qa_packet(public,c,v,'INC-6E627662CA32')['design']['qa_badges'])
    def test_public_intervention_whitelist(self):
        from . import exps
        from copy import deepcopy
        p=read_json(SOURCE/'INC-6E627662CA32.json');c=compile_case(p);before=deepcopy(c);v=comparison_provenance(c,p)
        qa=exps.qa_packet(p,c,v,'case');vs=exps.intervention_inputs(p,c,v,'case',qa)
        self.assertEqual(c,before)
        self.assertEqual(vs['POSITION']['evidence'],c['evidence']);self.assertEqual(vs['IRRELEVANT']['evidence'],c['evidence'])
        for name in ('BINDING','OPERAND','IRRELEVANT'):self.assertFalse(vs[name]['audit']['label_scoring_allowed'])
        orig={x['id']:x for x in c['evidence']['cards']}
        for card in vs['BINDING']['evidence']['cards']:
            self.assertEqual(card['data'],orig[card['id']]['data'])
        for name,r in vs.items():
            self.assertEqual({x['id'] for x in r['evidence']['cards']},set(orig))
    def test_quantiles_and_contrast_independent_oracle(self):
        from . import exps
        for a in ([0,0,0,0,0],[-10,-1,0,2,1e8],[1,2,3,4,5,6]):
            for q in (.1,.25,.5,.75,.9):self.assertAlmostEqual(exps.empirical_quantile(a,q),float(np.quantile(a,q,method='linear')))
        p=read_json(SOURCE/'INC-6E627662CA32.json');c=compile_case(p);inventory=exps.contrast_inventory(c,p)
        for row in inventory['rows']:
            r=np.array(row['phases']['reference']);u=np.array(row['phases']['current'])
            scale=1.4826*np.median(abs(r-np.median(r)))
            if scale==0:scale=(np.quantile(r,.75)-np.quantile(r,.25))/1.349
            np.testing.assert_allclose(row['change'],(np.quantile(u,[.1,.5,.9])-np.quantile(r,[.1,.5,.9]))/scale,rtol=1e-12,atol=1e-12)
    def test_atlas_ordered_columns_preserve_all_cards_and_bundle_adjacency(self):
        """Pending targeted regression: no row-end padding and no fact shrinking."""
        from . import exps
        from renderer.utils import compile_design
        from copy import deepcopy
        p=read_json(SOURCE/'INC-6E627662CA32.json');c=compile_case(p);original=deepcopy(c)
        atlas=exps.compile_atlas(p,c);self.assertEqual(c,original)
        self.assertEqual(atlas,exps.compile_atlas(p,c))
        a={r['card']:r for r in compile_design(c['evidence'],c['design'])['rectangles']}
        scene=compile_design(atlas['evidence'],atlas['design']);b={r['card']:r for r in scene['rectangles']}
        new={card['id']:card for card in atlas['evidence']['cards']}
        for card in c['evidence']['cards']:
            cid=card['id'];self.assertEqual(new[cid],card)
            self.assertEqual(b[cid]['width'],a[cid]['width']);self.assertGreaterEqual(b[cid]['height'],a[cid]['height'])
        self.assertLessEqual(scene['height'],8192);self.assertEqual(atlas['design']['font_size'],c['design']['font_size'])
        order=sorted(b,key=lambda cid:atlas['design']['indexing']['indices'][cid])
        self.assertEqual(order,sorted(b,key=lambda cid:(b[cid]['x'],b[cid]['y'])))
        ranks={entity:i for i,entity in enumerate(p['candidates'])}
        entity_order=[ranks[new[cid]['entity']] for cid in order if new[cid]['entity'] in ranks]
        self.assertEqual(entity_order,sorted(entity_order))
        for bundle in atlas['atlas_audit']['layout']['source_strip_bundles']:
            self.assertEqual(len({b[cid]['x'] for cid in bundle}),1)
            for left,right in zip(bundle,bundle[1:]):
                self.assertEqual(b[left]['y']+b[left]['height']+atlas['design']['gap'],b[right]['y'])
    def test_retained_variant_requires_pass_and_identical_inputs(self):
        from . import gates
        from .utils import save_json, stable_hash, digest
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);receipt=root/'old/qualification.json'
            save_json(receipt,{'status':'passed','input_tokens':120})
            variant={'evidence':{'value':0},'design':{'layout':'fixed'}}
            ref={'receipt':'old/qualification.json','sha256':digest(receipt),
                'evidence_hash':stable_hash(variant['evidence']),'design_hash':stable_hash(variant['design'])}
            with patch.object(gates,'ROOT',root):
                self.assertTrue(gates.retained_variant(variant,ref)['reused'])
                with self.assertRaises(ValueError):gates.retained_variant({**variant,'design':{'layout':'changed'}},ref)
                with self.assertRaises(ValueError):gates.retained_variant({**variant,'evidence':{'value':1}},ref)
                save_json(receipt,{'status':'failed'})
                with self.assertRaises(ValueError):gates.retained_variant(variant,ref)
                ref['sha256']=digest(receipt)
                with self.assertRaises(ValueError):gates.retained_variant(variant,ref)
    def test_qa_badge_validation_does_not_admit_answers(self):
        from . import exps
        from renderer.utils import compile_design
        p=read_json(SOURCE/'INC-6E627662CA32.json');c=compile_case(p);v=comparison_provenance(c,p);q=exps.qa_packet(p,c,v,'case')
        compile_design(c['evidence'],q['design'])
        q['design']['qa_badges'][0]['answer']=1
        with self.assertRaises(ValueError):compile_design(c['evidence'],q['design'])
    def test_transaction_resume_failure_reference_repeat_and_pause(self):
        from .utils import SingleCallRunner
        import socket
        from unittest.mock import patch
        good=json.dumps({'services':['101','102','103','104','105'],'reason':'fixture','confidence':'low'});seen=[]
        def provider(request):seen.append(request);return good if request.get('valid',True) else '{}'
        with tempfile.TemporaryDirectory() as folder,patch.object(socket,'create_connection',side_effect=AssertionError('CPU networking forbidden')):
            r=SingleCallRunner(folder,provider,20,offline=True);candidates=['101','102','103','104','105']
            first=lambda:{'seed':1};r.run('a',first,candidates,['102']);self.assertEqual(len(seen),1)
            self.assertEqual(r.run('a',lambda:1/0,candidates)['outcome']['metrics']['mrr'],.5)
            r.run('ref',first,candidates,reference='a');self.assertEqual(len(seen),1)
            with self.assertRaises(ValueError):r.run('badref',lambda:{'seed':2},candidates,reference='a')
            with self.assertRaises(ValueError):r.run('badrep',first,candidates,repeat=True,reference='a')
            r.run('rep',lambda:{'seed':2},candidates,repeat=True);self.assertEqual(len(seen),2)
            with self.assertRaises(RuntimeError):r.run('reply',first,candidates,fail_at='after_response')
            count=len(seen);self.assertEqual(len(r.recover()['recovered_without_generation']),1)
            r.run('reply',first,candidates);self.assertEqual(len(seen),count)
            with self.assertRaises(RuntimeError):r.run('marker',first,candidates,fail_at='before_commit')
            count=len(seen);r.run('marker',first,candidates);self.assertEqual(len(seen),count)
            with self.assertRaises(RuntimeError):r.run('lost',first,candidates,fail_at='before_provider')
            self.assertEqual(len(r.recover()['interrupted_spent_calls']),1)
            r.run('lost',first,candidates,retry=True)
            bad=r.run('invalid',lambda:{'valid':False},candidates);self.assertEqual(bad['outcome']['metrics']['mrr'],0)
            count=len(seen);r.run('invalid',lambda:1/0,candidates);self.assertEqual(len(seen),count)
            (Path(folder)/'PAUSE').touch();self.assertEqual(r.run('paused',lambda:1/0,candidates)['status'],'paused')
            (Path(folder)/'PAUSE').unlink();r.run('paused',first,candidates)
            with self.assertRaises(BlockingIOError):SingleCallRunner(folder,provider,20,offline=True)
            r.close()
            r=SingleCallRunner(folder,provider,20,offline=True);r.run('a',lambda:1/0,candidates);r.close()
    def test_batched_tensor_adapter_identity_padding_permutation(self):
        if importlib.util.find_spec('torch') is None:self.skipTest('torch is in infer CPU environment')
        import torch
        from .utils import pack_injected_batch
        ids=torch.tensor([[0,0,1,99,99,2],[1,99,99,99,99,2]]);mask=(ids!=0).long()
        pos=torch.stack([torch.arange(6).repeat(2,1)]*3);emb=ids[...,None].repeat(1,1,3).float()
        features=[torch.arange(n*3).reshape(n,3).float()+100 for n in (2,4)]
        full=pack_injected_batch(ids,mask,pos,emb,features,99,[list(range(2)),list(range(4))])
        pruned=pack_injected_batch(ids,mask,pos,emb,features,99,[[1],[0,3]])
        reverse=pack_injected_batch(ids.flip(0),mask.flip(0),pos.flip(1),emb.flip(0),features[::-1],99,[[0,3],[1]])
        torch.testing.assert_close(pruned['inputs_embeds'],reverse['inputs_embeds'].flip(0));torch.testing.assert_close(pruned['position_ids'],reverse['position_ids'].flip(1))
        self.assertEqual(full['inputs_embeds'].shape,(2,6,3));self.assertEqual(pruned['inputs_embeds'].shape,(2,4,3))
        self.assertEqual(pruned['plans'][0]['next_text_position'],full['plans'][0]['next_text_position'])
        with self.assertRaises(ValueError):pack_injected_batch(ids,mask,pos,emb,features,99,[[1,1],[0,3]])
    def test_gprune_against_frozen_reference_expression(self):
        if importlib.util.find_spec('torch') is None:self.skipTest('torch is in infer CPU environment')
        import torch
        from .utils import gprune_select
        x=np.random.default_rng(719).normal(size=(32,12)).astype(np.float32);x[0]=0
        f=torch.from_numpy(x);unit=torch.nn.functional.normalize(f,p=2,dim=1);a=unit@unit.T
        a[a<.5]=0;a/=.03;a[abs(a)<1e-6]=-5000;a=torch.nn.functional.softmax(a,dim=1)
        degree=(a>0).sum(1);score=(torch.linalg.norm(f,dim=-1)[None]@torch.matrix_power(a,5))/degree
        actual=gprune_select(x,12)
        np.testing.assert_allclose(actual['scores'],score[0].numpy(),rtol=2e-6,atol=2e-6)
        self.assertEqual(actual['indices'],sorted(score.topk(12).indices[0].tolist()))




class SmokeRuntime(unittest.TestCase):
    def test_frozen_slots_and_worker_authority(self):
        from .gates import smoke_runtime_config,smoke_worker_authority
        cfg=smoke_runtime_config()
        slots=[s for g in cfg['hf_groups'] for s in g['slots']]+[cfg['native_slot']['slot']]
        self.assertEqual(sorted(slots),list(range(1,19)))
        self.assertFalse(cfg['formal_enabled'])
        with self.assertRaises((FileNotFoundError,PermissionError)):smoke_worker_authority()

    def test_native_generation_midlayer_identity_and_short_cache(self):
        import torch
        from unittest.mock import patch
        from transformers.models.qwen3_5 import modeling_qwen3_5 as m
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5Config,Qwen3_5VisionConfig
        from .utils import injected_generate,hybrid_prior_generate,SmokeLogitsCapture,pack_injected_batch
        text=PriorCompletion.tiny_model()
        vision=Qwen3_5VisionConfig(depth=2,hidden_size=32,intermediate_size=64,num_heads=4,out_hidden_size=32,spatial_merge_size=2,patch_size=2,temporal_patch_size=1,num_position_embeddings=64)
        config=Qwen3_5Config(text_config=text.config.to_dict(),vision_config=vision.to_dict(),image_token_id=91,vision_start_token_id=90,vision_end_token_id=92)
        config._attn_implementation='sdpa'
        with patch.object(m,'FusedRMSNormGated',None):model=m.Qwen3_5ForConditionalGeneration(config).eval()
        model.model.language_model=text
        model.generation_config.pad_token_id=0;model.generation_config.eos_token_id=None
        batch={'input_ids':torch.tensor([[1,90,91,91,91,91,92,4]]),'attention_mask':torch.ones(1,8,dtype=torch.long),
            'image_grid_thw':torch.tensor([[1,4,4]]),'mm_token_type_ids':torch.tensor([[0,0,1,1,1,1,0,0]])}
        features=[torch.randn(4,32)];a=SmokeLogitsCapture();b=SmokeLogitsCapture()
        with torch.inference_mode():
            expected=injected_generate(model,batch,features,[list(range(4))],{'max_new_tokens':5,'do_sample':False,'logits_processor':[a]})
            positions,_=model.model.get_rope_index(batch['input_ids'],attention_mask=batch['attention_mask'],image_grid_thw=batch['image_grid_thw'],mm_token_type_ids=batch['mm_token_type_ids'])
            packed=pack_injected_batch(batch['input_ids'],batch['attention_mask'],positions,model.get_input_embeddings()(batch['input_ids']),features,91,[list(range(4))])
            prepared=injected_generate(model,batch,features,[list(range(4))],{'max_new_tokens':5,'do_sample':False},prepared=packed)
            self.assertTrue(torch.equal(prepared,expected))
            with self.assertRaisesRegex(ValueError,'selection differs'):
                injected_generate(model,batch,features,[[0,3]],{'max_new_tokens':5},prepared=packed)
            s2,state=hybrid_prior_generate(model,batch,features,4,'S2PRUNE',{'max_new_tokens':5,'do_sample':False},fixed_selection=list(range(4)))
            self.assertTrue(torch.equal(s2,expected))
            shortened,state=hybrid_prior_generate(model,batch,features,2,'S2PRUNE',{'max_new_tokens':5,'do_sample':False},fixed_selection=[0,3])
            self.assertEqual(shortened.shape,(1,5));self.assertEqual(state['trajectory'],[8,6,6,6])
            actual,state=hybrid_prior_generate(model,batch,features,4,'DART',{'max_new_tokens':5,'do_sample':False,'logits_processor':[b]},fixed_selection=list(range(4)))
            self.assertTrue(torch.equal(actual,expected))
            for step in a.values:torch.testing.assert_close(a.values[step],b.values[step],atol=2e-6,rtol=2e-6)
            short,state=hybrid_prior_generate(model,batch,features,2,'DART',{'max_new_tokens':5,'do_sample':False},fixed_selection=[0,3])
            self.assertEqual(short.shape,(1,5));self.assertEqual(state['input_tokens'],6)
            self.assertEqual(state['trajectory'],[8,8,6,6])
        self.assertNotIn('forward',text.__dict__)

    def test_passive_observer_preserves_padded_sdpa_mask(self):
        import torch
        from types import SimpleNamespace
        from .utils import PassiveAttentionTap,AttentionStore
        model=PriorCompletion.tiny_model();fake=SimpleNamespace(config=SimpleNamespace(text_config=model.config))
        ids=torch.tensor([[0,0,1,5,8,4],[1,5,7,2,8,4]]);mask=torch.tensor([[0,0,1,1,1,1],[1,1,1,1,1,1]])
        positions=(mask.cumsum(-1)-1).clamp_min(0)[None].expand(3,-1,-1)
        with torch.inference_mode():
            before=model(input_ids=ids,attention_mask=mask,position_ids=positions,use_cache=False).last_hidden_state
            with tempfile.TemporaryDirectory() as folder:
                store=AttentionStore(folder);tap=PassiveAttentionTap(store);tap.install(fake)
                after=model(input_ids=ids,attention_mask=mask,position_ids=positions,use_cache=False).last_hidden_state
                tap.close();store.close()
            torch.testing.assert_close(before,after,atol=0,rtol=0)


class SmokeGeometryRepair(unittest.TestCase):
    def test_actual_five_smoke_image_maps(self):
        import torch
        from .gates import smoke_attention_input
        root=Path('RQs/RQ4_1/results/comparison_coding_v1')
        requests=read_json(root/'smoke_geometry_repair_v19/revised_requests.json')
        self.assertEqual(len(requests),5)
        for key,req in requests.items():
            with self.subTest(key=key):
                batch=torch.load(root/'gpu_smoke_v18/inputs'/(key+'.pt'),map_location='cpu',weights_only=True,mmap=True)
                record=smoke_attention_input(req,batch['input_ids'][0].numpy())
                self.assertTrue(record['png_bytes_unchanged'])
                self.assertTrue(record['original_geometry_unchanged'])
                self.assertEqual(len(record['key_region']),req['input_tokens'])
                self.assertTrue(any(record['key_region']))

    def test_missing_map_rejected_before_call(self):
        from .gates import smoke_attention_input
        with self.assertRaisesRegex(ValueError,'no qualified attention map'):
            smoke_attention_input({'png_sha256':'dummy'},[1,2])

    def test_wrong_input_and_modified_map_rejected(self):
        import torch
        from .gates import smoke_attention_input
        root=Path('RQs/RQ4_1/results/comparison_coding_v1')
        requests=read_json(root/'smoke_geometry_repair_v19/revised_requests.json')
        key,req=next(iter(requests.items()))
        batch=torch.load(root/'gpu_smoke_v18/inputs'/(key+'.pt'),map_location='cpu',weights_only=True,mmap=True)
        with self.assertRaisesRegex(ValueError,'different input sequence'):
            smoke_attention_input(req,batch['input_ids'][0].numpy()[1:])
        with self.assertRaisesRegex(ValueError,'Frozen attention map changed'):
            smoke_attention_input({**req,'attention_map_sha256':'wrong'},batch['input_ids'][0].numpy())

    def test_old_header_error_is_not_silently_ignored(self):
        import torch
        from .utils import attention_key_regions
        root=Path('RQs/RQ4_1/results/comparison_coding_v1/gpu_smoke_v18')
        req=read_json(root/'freeze.json')['requests']['INC-6E627662CA32__BASE']
        batch=torch.load(root/'inputs/INC-6E627662CA32__BASE.pt',map_location='cpu',weights_only=True,mmap=True)
        grid=batch['image_grid_thw'][0].tolist()
        with self.assertRaisesRegex(ValueError,'Actual header geometry missing'):
            attention_key_regions(read_json(req['manifest']),(grid[1]//2,grid[2]//2),batch['input_ids'][0].numpy(),248056)


class SmokeRenewal(unittest.TestCase):
    def test_round_claim_is_exclusive_and_bounded(self):
        from unittest.mock import patch
        from . import gates
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            cfg={'authority':'user_2026_10_07_ten_additional_smokes','allowance':'allowance.json','round':1}
            save_json(root/'round.json',cfg)
            save_json(root/'allowance.json',{'authority':cfg['authority'],'additional_rounds':10,'calls_per_round':18,
                'seconds_per_round':600,'total_call_ceiling':12000,'registry':'claims','round_configs':{'1':'round.json'}})
            with patch.object(gates,'ROOT',root):
                gates.smoke_claim_round(cfg)
                with self.assertRaises(FileExistsError):gates.smoke_claim_round(cfg)
                with self.assertRaises(PermissionError):gates.smoke_claim_round({**cfg,'round':11})
                with self.assertRaisesRegex(ValueError,'not registered'):gates.smoke_claim_round({**cfg,'extra':'changed'})

    def test_reuse_requires_complete_unchanged_committed_group(self):
        from unittest.mock import patch
        from . import gates
        from .utils import digest
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);group={'slots':[1],'requests':['a'],'mode':'native'}
            result={'status':'completed','slot':1,'request_hash':'same'};save_json(root/'done.json',result)
            freeze={'requests':{'a':{'request_hash':'same'}},'reused_slots':{'1':{
                'completed':'done.json','completed_sha256':digest(root/'done.json'),'group_hash':stable_hash(group)}}}
            with patch.object(gates,'ROOT',root):
                self.assertEqual(gates.smoke_reuse_group(group,freeze)[0]['new_model_calls'],0)
                with self.assertRaisesRegex(ValueError,'partially reuse'):
                    gates.smoke_reuse_group({**group,'slots':[1,2],'requests':['a','b']},freeze)
                with self.assertRaisesRegex(ValueError,'contract changed'):
                    gates.smoke_reuse_group({**group,'mode':'changed'},freeze)
                result['status']='started';save_json(root/'done.json',result)
                with self.assertRaisesRegex(ValueError,'completion changed'):gates.smoke_reuse_group(group,freeze)


class SmokeNativeRepair(unittest.TestCase):
    def test_native_schema_has_identical_hf_grammar_and_strict_host_validation(self):
        import xgrammar as xgr
        import jsonschema
        from vllm.v1.structured_output.backend_xgrammar import has_xgrammar_unsupported_json_features,validate_xgrammar_grammar
        from vllm.sampling_params import SamplingParams,StructuredOutputsParams
        from .gates import smoke_native_schema
        from .utils import rca_schema
        original=rca_schema();wire=smoke_native_schema()
        self.assertTrue(has_xgrammar_unsupported_json_features(original))
        self.assertFalse(has_xgrammar_unsupported_json_features(wire))
        self.assertEqual(str(xgr.Grammar.from_json_schema(original,any_whitespace=False)),str(xgr.Grammar.from_json_schema(wire,any_whitespace=False)))
        validate_xgrammar_grammar(SamplingParams(structured_outputs=StructuredOutputsParams(json=wire)))
        duplicate={'services':['1']*5,'reason':'test','confidence':'low'}
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(duplicate,rca_schema())

    def test_readiness_uses_auth_and_rejects_auth_errors(self):
        import io
        from unittest.mock import patch
        from urllib.error import HTTPError,URLError
        from .gates import smoke_probe_models
        url='http://127.0.0.1:8000/v1/models'
        def opened(request,timeout):
            self.assertEqual(request.get_header('Authorization'),'Bearer test-local-only')
            return io.BytesIO(b'{"data":[{"id":"Qwen/Qwen3.8-27B"}]}')
        with patch('urllib.request.urlopen',side_effect=opened):
            self.assertEqual(smoke_probe_models(url,'test-local-only')['data'][0]['id'],'Qwen/Qwen3.8-27B')
        for code in (401,403,404):
            with patch('urllib.request.urlopen',side_effect=HTTPError(url,code,'test',{},None)):
                with self.assertRaisesRegex(RuntimeError,str(code)):smoke_probe_models(url,'test-local-only')
        for error in (HTTPError(url,503,'starting',{},None),URLError('starting')):
            with patch('urllib.request.urlopen',side_effect=error):self.assertIsNone(smoke_probe_models(url,'test-local-only'))

    def test_committed_hf_phase_skips_model_load_only_if_complete(self):
        from unittest.mock import patch
        from . import gates
        from .utils import digest
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);report={'status':'passed','completed':2,'attention_error':None,'attention_missed':0}
            save_json(root/'hf.json',report)
            freeze={'config':{'hf_groups':[{'slots':[1,2]}]},'hf_report_reference':{'path':'hf.json','sha256':digest(root/'hf.json')}}
            with patch.object(gates,'ROOT',root):
                self.assertEqual(gates.smoke_reused_hf_report(freeze,[{'slot':1},{'slot':2}])['new_model_calls'],0)
                with self.assertRaisesRegex(ValueError,'Incomplete reused'):gates.smoke_reused_hf_report(freeze,[{'slot':1}])
                report['attention_error']='incomplete';save_json(root/'hf.json',report)
                freeze['hf_report_reference']['sha256']=digest(root/'hf.json')
                with self.assertRaisesRegex(ValueError,'Unqualified reused'):gates.smoke_reused_hf_report(freeze,[{'slot':1},{'slot':2}])


class DeploymentRuntime(unittest.TestCase):
    def test_durable_reply_and_ledger_recovery_never_resample(self):
        from .utils import DeploymentJournal
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);req={'request_hash':'immutable'};unit={'key':'first'}
            score=lambda request,response:{'valid':False,'rr':0,'response':response}
            journal=DeploymentJournal(root,4,'test',score)
            call=journal.begin(unit,req)
            with self.assertRaisesRegex(RuntimeError,'durable raw'):
                journal.commit(unit,req,{'response':'bad model answer'},call,fail_at='after_reply')
            journal.close();journal=DeploymentJournal(root,4,'test',score)
            self.assertEqual(journal.recover()['recovered'],['first'])
            self.assertIsNone(journal.begin(unit,req))
            self.assertEqual(journal.calls.summary(),{'complete':1})
            self.assertEqual(read_json(root/'completed/first.json')['outcome']['rr'],0)
            second={'key':'second'};call=journal.begin(second,req)
            with self.assertRaisesRegex(RuntimeError,'ledger commit'):
                journal.commit(second,req,{'response':'another'},call,fail_at='after_ledger')
            journal.close();journal=DeploymentJournal(root,4,'test',score)
            self.assertEqual(journal.recover()['recovered'],['second'])
            journal.finish_phase('hf',[unit,second]);self.assertTrue((root/'phase_complete.hf.json').exists())
            self.assertEqual(journal.calls.summary(),{'complete':2});journal.close()

    def test_interrupted_attempt_spends_budget_and_phase_needs_drain(self):
        from .utils import DeploymentJournal
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);req={'request_hash':'x'};unit={'key':'x'}
            journal=DeploymentJournal(root,2,'test',lambda *_:{'valid':True})
            journal.begin(unit,req)
            with self.assertRaises(RuntimeError):journal.begin(unit,req)
            with self.assertRaises(ValueError):journal.finish_phase('hf',[unit])
            journal.close();journal=DeploymentJournal(root,2,'test',lambda *_:{'valid':True})
            self.assertEqual(journal.recover()['interrupted_spent_attempts'],['x'])
            call=journal.begin(unit,req);journal.submit(unit,req,{'response':'done'},call)
            journal.finish_phase('hf',[unit])
            self.assertEqual(journal.calls.summary(),{'complete':1,'interrupted':1})
            with self.assertRaises(RuntimeError):journal.begin({'key':'exhausted'},req)
            journal.close()

    def test_concurrent_native_commits_and_duplicate_owner(self):
        from concurrent.futures import ThreadPoolExecutor
        from .utils import DeploymentJournal
        with tempfile.TemporaryDirectory() as folder:
            journal=DeploymentJournal(folder,18,'test',lambda *_:{'valid':True})
            with self.assertRaises(BlockingIOError):DeploymentJournal(folder,18,'test',lambda *_:{})
            def submit(i):
                unit={'key':str(i)};req={'request_hash':str(i)}
                call=journal.begin(unit,req);journal.submit(unit,req,{'response':str(i)},call)
            with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(submit,range(18)))
            journal.finish_phase('native',[{'key':str(i)} for i in range(18)])
            self.assertEqual(journal.calls.summary(),{'complete':18});journal.close()

    def test_fast_resume_and_pause_do_not_materialize_or_load_model(self):
        import os
        from unittest.mock import patch
        from . import gates
        from .utils import digest
        for already_complete in (True,False):
            with tempfile.TemporaryDirectory() as folder:
                root=Path(folder);out=root/'run';out.mkdir()
                cfg={'purpose':'qualification','output':'run','index':'index.json','max_calls':18,'ledger_scope':'test',
                    'test_units':[{'key':'one','backend':'hf'}]}
                save_json(root/'index.json',{'cases':{},'units':[]})
                save_json(out/'started.json',{'config_hash':stable_hash(cfg)})
                if already_complete:save_json(out/'completed/one.json',{'unchanged':True})
                else:(out/'PAUSE').touch()
                with patch.object(gates,'ROOT',root),patch.object(gates,'deployment_config',return_value=cfg),patch.dict(os.environ,{'CANVASRCA_RQ41_WORKER_TOKEN':digest(out/'started.json')}),patch.object(gates,'deployment_hf_worker',side_effect=AssertionError('loaded')):
                    self.assertFalse(gates.deployment_worker('hf')['model_loaded'])

    def test_launch_and_new_window_limits_fail_closed(self):
        import os,copy
        from unittest.mock import patch
        from . import gates
        original=read_json('RQs/RQ4_1/configs/deployment_v26.json')
        with self.assertRaisesRegex(PermissionError,'awaits explicit'):gates.deployment_config()
        cfg={**original,'purpose':'qualification','authority':'user_2026_10_07_two_deployment_smokes','round':1,'max_calls':18,'wall_seconds':600,'test_units':[{'key':'x'}]}
        accepted=read_json('RQs/RQ4_1/configs/runtime_acceptance_v26.json')
        for field,value,error in [('round',3,PermissionError),('max_calls',19,ValueError),('wall_seconds',601,ValueError),('generation',{'max_new_tokens':8192,'temperature':.5,'top_p':.95,'top_k':0},ValueError)]:
            changed=copy.deepcopy(cfg);changed[field]=value
            with patch.dict(os.environ,{'CANVASRCA_RQ41_DEPLOYMENT_CONFIG':'config'}),patch.object(gates,'read_json',side_effect=[changed,accepted]):
                with self.assertRaises(error):gates.deployment_config()

    def test_dispatch_and_corrupted_controls_do_not_load_private_labels(self):
        from unittest.mock import patch
        from . import gates
        units=read_json('RQs/RQ4_1/configs/remaining_logical_inputs_v6.json')['positions']
        arms={u['arm'] for u in units};self.assertEqual(len(arms),22)
        for arm in arms:
            unit={**next(u for u in units if u['arm']==arm),'queue_index':1,'request_key':'test'}
            group=gates.deployment_group(unit)
            self.assertEqual(group['mode'],'text' if arm.startswith('T_') else 'prior' if arm in {'DART_E50','S2PRUNE_E50'} else 'native' if arm in {'V_FULL','CONTRAST_ATLAS'} else 'select')
        with patch.object(gates,'read_json',side_effect=AssertionError('private label read')):
            result=gates.smoke_score({'id':'id','variant':'BINDING','label_scoring_allowed':False},'{"services":["1","2","3","4","5"],"reason":"test","confidence":"low"}',{'id':{'candidates':['1','2','3','4','5']}})
            self.assertFalse(result['original_root_labels_used'])

class NativePrefixIsolation(unittest.TestCase):
    def test_actual_vllm_adapter_add_swap_remove_and_release(self):
        import torch
        from types import SimpleNamespace
        from unittest.mock import patch
        from vllm import SamplingParams
        from vllm.v1.sample.logits_processor import BatchUpdate,MoveDirectionality
        from .utils import VLLMRankingPrefix
        class Tokens:
            def decode(self,ids,**kw):return ''.join(chr(i) for i in ids)
        with patch('transformers.AutoTokenizer.from_pretrained',return_value=Tokens()):
            adapter=VLLMRankingPrefix(SimpleNamespace(model_config=SimpleNamespace(tokenizer='fixture')),torch.device('cpu'),False)
        params=SamplingParams(extra_args={'rq41_ranking_profile':'ranking_prefix_greedy_v25'})
        a=[];b=[];prompt=[ord(c) for c in '{"services":["1","2","3","4","5"]']
        adapter.update_state(BatchUpdate(2,[],[(0,params,prompt,a),(1,params,prompt,b)],[]))
        scores=torch.tensor([[1.,3.,2.],[5.,1.,2.]])
        self.assertEqual(torch.isfinite(adapter.apply(scores.clone())).sum(-1).tolist(),[1,1])
        a.extend(prompt)
        self.assertEqual(torch.isfinite(adapter.apply(scores.clone())).sum(-1).tolist(),[3,1])
        adapter.update_state(BatchUpdate(2,[],[],[(0,1,MoveDirectionality.SWAP)]))
        self.assertEqual(torch.isfinite(adapter.apply(scores.clone())).sum(-1).tolist(),[1,3])
        adapter.update_state(BatchUpdate(1,[1],[],[]))
        self.assertEqual(torch.isfinite(adapter.apply(scores[:1].clone())).sum().item(),1)
        b.extend(prompt)
        self.assertEqual(torch.isfinite(adapter.apply(scores[:1].clone())).sum().item(),3)
        with self.assertRaises(ValueError):adapter.new_req_logits_processor(SamplingParams())


class NativeSeedRepair(unittest.TestCase):
    def test_default_contract_and_explicit_seed_fail_closed(self):
        from vlmrca.vlm.runtime_contract import assert_request_sampling, VLLMRuntimeContractError
        assert_request_sampling(temperature=1.,top_p=.95,seed=42)
        for seed in (981455851,1792866966):
            with self.assertRaises(VLLMRuntimeContractError):
                assert_request_sampling(temperature=1.,top_p=.95,seed=seed)
            assert_request_sampling(temperature=1.,top_p=.95,seed=seed,registered_seed=seed)
            for temp,prob,expected in ((.5,.95,seed),(1.,.9,seed),(1.,.95,42)):
                with self.assertRaises(VLLMRuntimeContractError):
                    assert_request_sampling(temperature=temp,top_p=prob,seed=seed,registered_seed=expected)
        for bad in (True,1.5,'42',-1,2**63):
            with self.assertRaises(VLLMRuntimeContractError):
                assert_request_sampling(temperature=1.,top_p=.95,seed=42,registered_seed=bad)

    def test_all_registered_native_seeds_reach_transport_without_global_mutation(self):
        import os
        from concurrent.futures import ThreadPoolExecutor
        from unittest.mock import patch
        from vlmrca.vlm import client
        from vlmrca.vlm.configs import VLMConfig
        from unified_scripts.vllm_inference import VLLMInferenceConfig
        from . import gates
        cfg=read_json('RQs/RQ4_1/configs/deployment_v28.json');index=read_json(cfg['index'])
        units=gates.deployment_units(cfg,index,'native');self.assertEqual(len(units),220)
        before=VLLMInferenceConfig.load().data['common'].copy()
        def transport(api,payload,recipe,*args):
            self.assertEqual(payload['seed'],recipe.seed)
            self.assertEqual((payload['temperature'],payload['top_p']),(1.,.95))
            self.assertNotIn('registered_seed',payload)
            return client.VLMResponse(text=str(payload['seed']))
        def infer(unit):
            recipe=VLMConfig(tag='qwen3.8-27b',backend='openai',model_id='fixture',
                temperature=1.,top_p=.95,seed=unit['seed'],base_url_env='RQ41_TEST_URL')
            result=client.call_vlm([{'type':'text','text':'static test'}],recipe,max_retries=1,
                record_performance=True,registered_seed=unit['seed'])
            return int(result.text)
        with patch.dict(os.environ,{'RQ41_TEST_URL':'http://127.0.0.1:1/v1'}), \
             patch.object(client,'load_env'),patch('openai.OpenAI'), \
             patch.object(client,'attention_probe_enabled',return_value=False), \
             patch.object(client,'_call_openai_streaming',side_effect=transport):
            with ThreadPoolExecutor(max_workers=36) as pool:observed=list(pool.map(infer,units))
        self.assertEqual(observed,[u['seed'] for u in units])
        self.assertEqual(VLLMInferenceConfig.load().data['common'],before)

    def test_native_worker_forwards_frozen_seed_through_real_client(self):
        import os
        from types import SimpleNamespace as NS
        from unittest.mock import patch,MagicMock
        from vlmrca.vlm import client
        from . import gates
        cfg=read_json('RQs/RQ4_1/configs/deployment_v28.json')
        unit={'key':'seed-fixture','seed':1792866966}
        req={'parts':[{'type':'text','text':'static test'}],'system':'task','input_tokens':9}
        observed=[]
        def transport(api,payload,recipe,*args):
            observed.append(payload)
            return client.VLMResponse(text='{"services":[]}',input_tokens=9,output_tokens=4)
        journal=MagicMock();journal.scope='fixture';journal.completed.return_value=False;journal.begin.return_value=1
        server=MagicMock();server.pid=123456;server.poll.return_value=None
        sock=MagicMock();sock.connect_ex.return_value=1
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{},clear=False), \
             patch('subprocess.Popen',return_value=server),patch('socket.socket',return_value=sock), \
             patch('os.killpg'),patch('openai.OpenAI'),patch.object(client,'load_env'), \
             patch.object(client,'attention_probe_enabled',return_value=False), \
             patch.object(client,'_call_openai_streaming',side_effect=transport), \
             patch.object(gates,'smoke_probe_models',return_value={'data':[{'id':'Qwen/Qwen3.8-27B'}]}), \
             patch.object(gates,'deployment_bound_request',return_value=req), \
             patch.object(gates,'read_json',return_value={'ranking_complete':True}):
            report=gates.deployment_native_worker(cfg,{},Path(folder),journal,[unit],lambda:False)
        self.assertEqual(report['completed_this_session'],1)
        self.assertEqual(observed[0]['seed'],unit['seed'])
        self.assertEqual(observed[0]['extra_body']['top_k'],-1)
        self.assertEqual(observed[0]['max_completion_tokens'],8192)
        raw=journal.submit.call_args.args[2]
        self.assertEqual(raw['decoder_seed'],raw['recipe']['seed'])
        self.assertEqual(raw['decoder_seed'],unit['seed'])


if __name__=='__main__':unittest.main()
