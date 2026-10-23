"""Registered future regressions. Static checks never import or run this suite."""
import unittest,json,tempfile,os
from pathlib import Path
from unittest.mock import patch


class DomainOperators(unittest.TestCase):
    def setUp(self):
        from .utils import domain_packet
        self.base={'anchors':[0,1,8],'evidence':[2,3,9,10],'image_tokens':64,'grid':[8,8],'retained':[0,1,2,8,10],'groups':[],'operator':'gather'}
        self.geometry={'panels':[{'card':'c1','box':[0,0,2048,2048]},{'card':'c2','box':[2048,0,2048,2048]}]}
        self.domain=domain_packet(self.base,self.geometry,ink=[4,12,20])
    def test_outside_partition_and_capacity(self):
        from .utils import outside_groups
        # b=1 but three regions: must fail, never silently merge semantics.
        with self.assertRaises(ValueError):outside_groups(self.domain)
        domain=dict(self.domain,domain=list(range(80)),outside=list(range(80,100)),regions={'r':list(range(80,100))},grid=[10,10])
        groups=outside_groups(domain)
        self.assertEqual(len(groups),4);self.assertEqual(sorted(i for g in groups for i in g['members']),list(range(80,100)))
    def test_domain_pruning_is_exact(self):
        from .utils import context_plan
        p=context_plan(self.base,self.domain,'P_INK','fixture');self.assertEqual(p['retained'],sorted(set(self.domain['domain'])|{4,12,20}))
        length=context_plan(self.base,self.domain,'P_LENGTH_CONTROL','fixture')
        self.assertEqual(len(length['retained']),len(self.domain['domain']));self.assertTrue(set(self.base['anchors'])<=set(length['retained']))
    def test_empty_outside_alias(self):
        from .utils import context_plan,domain_packet,computation_identity
        base=dict(self.base,anchors=list(range(64)),evidence=[])
        domain=domain_packet(base,self.geometry)
        f=context_plan(base,domain,'F_O_FEATURE','fixture');p=context_plan(base,domain,'P_DOMAIN','fixture')
        self.assertEqual(computation_identity(f),computation_identity(p))
    def test_shared_token_region_signature(self):
        from .utils import domain_packet
        g={'panels':[{'card':'left','box':[0,0,530,1024]},{'card':'right','box':[530,0,1000,1024]}]}
        d=domain_packet(dict(self.base,anchors=[0],evidence=[]),g)
        self.assertIn('left|right',d['regions'])
    def test_feature_groups_and_fp32_mean(self):
        import torch
        from .utils import assign_feature_groups
        from .exps import fusion_means,encode_operators
        features=torch.tensor([[4,0],[0,4],[1,0],[1,0],[0,1],[0,1],[0,0],[0,0]],dtype=torch.bfloat16)
        plan={'operator':'outside_mean','anchors':[0],'evidence':[1],'image_tokens':8,'grid':[2,4],
            'outside':[2,3,4,5,6,7],'groups':[{'representative':2,'members':[2,3,6]},{'representative':4,'members':[4,5,7]}],
            'retained':[0,1,2,4],'assignment':'feature','sham':False,'sham_seed':'fixed'}
        groups=assign_feature_groups(features,plan);self.assertEqual(sorted(i for g in groups for i in g['members']),plan['outside'])
        for g in groups:self.assertIn(g['representative'],g['members'])
        sham=assign_feature_groups(features,dict(plan,sham=True));self.assertEqual([len(g['members']) for g in groups],[len(g['members']) for g in sham])
        actual=features.clone();fusion_means(actual,groups)
        self.assertTrue(torch.equal(actual[:2],features[:2]))
        for g in groups:torch.testing.assert_close(actual[g['representative']],sum(features[i].float() for i in g['members']).div(len(g['members'])).to(torch.bfloat16),rtol=0,atol=0)
        class Vision:
            calls=0
            def __call__(self,*args,**kwargs):self.calls+=1;return features.clone()
        vision=Vision();encoded,receipt=encode_operators(vision,None,torch.tensor([[1,4,8]]),{'operators':[plan]})
        self.assertEqual(vision.calls,1);self.assertTrue(torch.equal(encoded[:2],features[:2]));self.assertTrue(receipt[0]['resolved_assignment'])


class AttentionContract(unittest.TestCase):
    def test_mass_and_matched_background(self):
        import numpy as np,torch
        from .utils import redistribute_reference
        from .exps import torch_redistribute
        p=np.array([[.1,.2,.1,.3,.1,.2],[.5,.1,.1,.1,.1,.1],[1.,0,0,0,0,0]])
        masses={}
        for arm in ('S_O_REDIST','S_O_MASK','S_SINK_REDIST','S_BG_REDIST'):
            expected,audit=redistribute_reference(p,[1,2,3,4],[1,2],[3],arm)
            got,_,mass=torch_redistribute(torch.tensor(p)[:,None,:],[1,2,3,4],[1,2],[3],arm)
            np.testing.assert_allclose(got[:,0].numpy(),expected,atol=1e-12);np.testing.assert_allclose(expected.sum(-1),1)
            self.assertTrue((expected>=-1e-12).all());masses[arm]=mass
        torch.testing.assert_close(masses['S_SINK_REDIST'],masses['S_BG_REDIST'])
    def test_no_sink_does_not_disable_all_outside_arm(self):
        import numpy as np
        from .utils import redistribute_reference
        p=np.array([[.1,.3,.4,.2]])
        out,audit=redistribute_reference(p,[1,2],[1],[],'S_O_REDIST')
        self.assertAlmostEqual(out[0,1],.7);self.assertAlmostEqual(audit[0]['released'],.4)


class QAContract(unittest.TestCase):
    def question(self,mode='single'):
        return {'id':'q1','question':'In card 03, which entity owns this observation?','type':'id','mode':mode,
            'solutions':[['145','394']] if mode=='required_values' else [['145']],'id_domain':['145','394','993'],
            'proof':{'binding':'TRA1.entity','display':'145'},'support_cards':['TRA1']}
    def test_lenient_ids_and_half_credit(self):
        from .utils import score_qa
        q=self.question('required_values')
        for text in ['{"answers":[{"id":"q1","answer":["145","INVALID"]}]}','Answer: 145']:
            s=score_qa(text,[q]);self.assertEqual(s['end_to_end_credit'],.5)
        self.assertEqual(score_qa('Answer: [145, 993]',[q])['end_to_end_credit'],0)
        self.assertEqual(score_qa('```json\n{answers: [{id:"q1",answer:[145,394],},],}\n```',[q])['end_to_end_credit'],1)
    def test_no_oracle_in_receiver(self):
        from .utils import receive_qa,public_qa_items,score_qa
        q=self.question()
        with self.assertRaises(ValueError):receive_qa('145',[q])
        self.assertEqual(score_qa('The answer is 145.',[q])['end_to_end_credit'],1)
        self.assertEqual(score_qa('Answer: 145\nAnswer: 394',[q])['end_to_end_credit'],0)
        self.assertEqual(score_qa('{"answers":[{"id":"q99","answer":"394"},{"id":"q1","answer":"145"}]}',[q])['end_to_end_credit'],1)
        self.assertEqual(receive_qa('q99: 145',public_qa_items([q]))['answers'],{})
    def test_zero_and_units(self):
        from .utils import score_qa,validate_qa_item
        q=dict(self.question(),type='number',solutions=[['0']],id_domain=None,display_tolerance='0',unit_factors={'ms':1})
        self.assertEqual(score_qa('Answer: 0 ms',[q])['end_to_end_credit'],1)
        with self.assertRaises(ValueError):validate_qa_item(dict(q,solutions=[['']]))
    def test_distinct_correct_alternatives(self):
        from .utils import score_qa
        q=dict(self.question(),mode='alternatives',solutions=[['145'],['394']])
        self.assertEqual(score_qa('394',[q])['end_to_end_credit'],1)
        self.assertEqual(score_qa('[145, 394]',[q])['end_to_end_credit'],0)
    def test_displayed_numeric_units_and_sentence_punctuation(self):
        from .utils import score_qa
        from .exps import numeric_unit_factors
        q=dict(self.question(),type='number',solutions=[['1000']],id_domain=None,
            display_tolerance='0',unit_factors=numeric_unit_factors('µs'))
        for raw in ('1000 µs','1000 microseconds','1 ms','The answer is 1000.'):
            self.assertEqual(score_qa(raw,[q])['end_to_end_credit'],1,raw)
        self.assertEqual(score_qa('1000 ms',[q])['end_to_end_credit'],0)
    def test_metric_phase_prose_is_not_two_answers(self):
        from .utils import score_qa
        q=dict(self.question(),type='string',solutions=[['current']],id_domain=None,
            answer_vocabulary={'regular':'regular','current':'current','equal':'equal'})
        for raw in ('current is higher than regular','regular is lower than current','current > regular'):
            self.assertEqual(score_qa(raw,[q])['end_to_end_credit'],1,raw)
        self.assertEqual(score_qa('regular > current',[q])['end_to_end_credit'],0)


class DurableState(unittest.TestCase):
    def test_atomic_interruption_and_real_repeat(self):
        from . import utils
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'commit.json';utils.save(p,{'old':1})
            with patch.object(utils.os,'replace',side_effect=OSError('injected before commit')):
                with self.assertRaises(OSError):utils.save(p,{'new':2})
            self.assertEqual(utils.read(p),{'old':1})
            known={};record={'item':{'force_call':True},'generation_identity':'x','raw':'answer'}
            self.assertFalse(utils.remember_reference(known,'repeat',record));self.assertEqual(known,{})
            record['item']['force_call']=False;self.assertTrue(utils.remember_reference(known,'real',record));self.assertEqual(known,{'x':'real'})
    def test_storage_objects_are_plain_and_deduplicated(self):
        from . import utils
        with tempfile.TemporaryDirectory(dir=utils.ROOT) as tmp,patch.object(utils,'RESULTS',Path(tmp)):
            a,sha=utils.object_json({'raw':'invalid answer','messages':[{'role':'user','content':'exact text'}]});b,_=utils.object_json({'raw':'invalid answer','messages':[{'role':'user','content':'exact text'}]})
            self.assertEqual(a,b);self.assertEqual(utils.digest(utils.ROOT/a),sha);self.assertEqual(len(list((Path(tmp)/'objects').iterdir())),1)


def run():
    from .gates import require_authorization,execution_fingerprint
    from .utils import RESULTS,save
    require_authorization('cpu');os.environ['CUDA_VISIBLE_DEVICES']=''
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__,fromlist=['*']))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'status':'passed' if result.wasSuccessful() else 'blocked','fingerprint':execution_fingerprint(),
        'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'new_model_calls':0}
    save(RESULTS/'qualification/unit.json',report)
    if not result.wasSuccessful():raise RuntimeError('CPU regressions failed')
    return report
