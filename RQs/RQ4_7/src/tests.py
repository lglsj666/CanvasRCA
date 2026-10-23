"""Future CPU regressions. Importing this module never executes a test."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from . import utils,exps


def inventory():
    return {'A':{'box':[0,0,100,100],'readable':True,'scale':1,
                  'tiles':{'CLOSED':{'width':100,'height':100},'COMPARE':{'width':100,'height':150}},
                  'source_id':'a','sources':['a'],'modality':'M','role_keys':[['a','p95','current']],
                  'scale_ids':['duration']},
            'B':{'box':[100,0,100,100],'readable':True,'scale':1,
                  'tiles':{'CLOSED':{'width':100,'height':100},'COMPARE':{'width':100,'height':150}},
                  'source_id':'b','sources':['b'],'modality':'M','role_keys':[['b','p95','reference']],
                  'scale_ids':['duration']}}


def fake_request(identity='same',task='ACTION'):
    return {'identity':identity,'task':task,'arm':'PLAN','images':[],'image_sha256':[],
            'prompt':'offline fixture only','input_tokens':5,'max_output_tokens':512}


class SourceContracts(unittest.TestCase):
    def test_valid_action_and_original_pixel_box(self):
        response=json.dumps({'actions':[{'operation':'compare','regions':[[0,0,500,1000],[500,0,1000,1000]]}]})
        result=exps.plan_actions(response,inventory(),[200,100])
        self.assertEqual(len(result['groups']),1)
        self.assertEqual(result['groups'][0]['cards'],['A','B'])
        self.assertEqual(result['groups'][0]['regions'][1]['box'],[100.,0.,100.,100.])

    def test_outside_coordinate_is_not_clamped(self):
        result=exps.plan_actions('{"actions":[{"operation":"focus","regions":[[-1,0,500,1000]]}]}',inventory(),[200,100])
        self.assertEqual(result['groups'],[])

    def test_cross_panel_region_not_assigned_to_nearest(self):
        response='{"actions":[{"operation":"focus","regions":[[250,0,750,1000]]}]}'
        self.assertEqual(exps.plan_actions(response,inventory(),[200,100])['groups'],[])

    def test_bad_geometry_does_not_discard_an_independent_valid_action(self):
        response={'actions':[{'operation':'focus','regions':[[400,0,300,100]]},
                             {'operation':'focus','regions':[[500,0,1000,1000]]}]}
        result=exps.plan_actions(json.dumps(response),inventory(),[200,100])
        self.assertEqual([g['cards'] for g in result['groups']],[['B']])

    def test_repeated_source_never_increases_source_budget(self):
        response={'actions':[{'operation':'focus','regions':[[0,0,500,1000]]}]*2}
        result=exps.plan_actions(json.dumps(response),inventory(),[200,100])
        self.assertEqual(len(result['groups']),1)

    def test_capacity_skips_whole_group_without_shrinking(self):
        from renderer.operations.source_workspace import group_layout
        value=inventory();value['A']['tiles']['COMPARE']['width']=2200
        value['A']['tiles']['CLOSED']['width']=2200
        groups=[{'cards':['A','B'],'regions':[]}]
        admitted,rejected=group_layout(groups,value)
        self.assertEqual(admitted,[])
        self.assertEqual(len(rejected),1)
        self.assertEqual(value['A']['tiles']['COMPARE']['width'],2200)

    def test_closed_fallback_does_not_reserve_unused_comparison_annotation(self):
        from renderer.operations.source_workspace import group_layout
        value=inventory();value['A']['tiles']['COMPARE']['height']=1900
        admitted,rejected=group_layout([{'cards':['A'],'regions':[]},{'cards':['B'],'regions':[]}],value)
        self.assertEqual(len(admitted),2)
        self.assertEqual(admitted[1]['placements'][0]['y'],132)
        self.assertEqual(rejected,[])

    def test_two_full_sources_can_stack_and_do_not_shrink(self):
        from renderer.operations.source_workspace import group_layout
        value=inventory()
        for v in value.values():
            v['tiles']['CLOSED'].update(width=1340,height=600)
            v['tiles']['COMPARE'].update(width=1340,height=1300)
        admitted,rejected=group_layout([{'cards':['A','B'],'regions':[]}],value)
        self.assertEqual(admitted[0]['layout'],'vertical')
        self.assertEqual([p['width'] for p in admitted[0]['placements']],[1340,1340])
        self.assertEqual([p['y'] for p in admitted[0]['placements']],[16,632])
        self.assertEqual(rejected,[])

    def test_comparison_annotations_can_fall_back_to_complete_sources_for_capacity(self):
        from renderer.operations.source_workspace import group_layout
        value=inventory()
        for cid,v in value.items():
            v['tiles']['CLOSED'].update(width=1340,height=600)
            v['tiles']['COMPARE'].update(width=1340,height=1300,rows=[{
                'scale_id':'same','entity':cid,'source':cid,'statistic':'p95','phase':'current'}])
        admitted,rejected=group_layout([{'cards':['A','B'],'regions':[]}],value)
        self.assertEqual(admitted[0]['effective_mode'],'CLOSED')
        self.assertTrue(admitted[0]['comparison_capacity_fallback'])
        self.assertEqual(rejected,[])

    def test_selector_ignores_non_registered_outcome_values(self):
        a=inventory();b=inventory()
        b['A'].update(historical_mrr=1,anomaly=100000,root=True,value='999999')
        self.assertEqual(exps.deterministic_actions(a,[200,100]),
                         exps.deterministic_actions(b,[200,100]))

    def test_unknown_public_card_structure_fails(self):
        evidence={'schema':'CanvasEvidenceV1','cards':[{'id':'X','kind':'metric','title':'x',
            'entity':'123','unit':'ms','data':{},'private_root':'123'}]}
        with self.assertRaises(ValueError):
            exps.source_rows(evidence,{'roles':[]})

    def test_numeric_lexeme_and_statistic_not_rounded_or_relabelled(self):
        card={'id':'X','kind':'metric','title':'latency','entity':'123','unit':'ms',
              'data':{'details':[{'name':'p50','value':'0.0100'},{'name':'p95','value':'1e+2'}]}}
        roles=[{'entity':'123','source_occurrence':'one','signal':'latency','unit':'ms',
                'quantity':'latency','phase':'current','targets':[{'binding':f'X.detail.{i}'}]}
               for i in range(2)]
        rows=exps.source_rows({'schema':'CanvasEvidenceV1','cards':[card]},{'roles':roles})['X']
        self.assertEqual([r['value'] for r in rows],['0.0100','1e+2'])
        self.assertEqual([r['statistic'] for r in rows],['p50','p95'])
        self.assertNotEqual(rows[0]['scale_id'],rows[1]['scale_id'])

    def test_finite_geometry_rejects_nan_and_bool(self):
        from renderer.operations.source_workspace import finite_box
        for box in ([0,0,float('nan'),1],[False,0,1,1],[0,0,0,1],[0,0,101,1]):
            with self.assertRaises(ValueError):
                finite_box(box,100,100)


class OutputAndGeometry(unittest.TestCase):
    def test_unknown_prefix_task_template_fails_instead_of_conflicting(self):
        with self.assertRaises(ValueError):
            exps.task_adapter('Unrecognized original schema','S_GROUND')
        self.assertEqual(exps.task_adapter('unchanged','M_COMPARE'),'unchanged')

    def test_prefix_services_mention_does_not_trigger_ranking(self):
        self.assertEqual(utils.ranking_segment('{"notes":["services [not a ranking]"],'), 'before')
        self.assertEqual(utils.ranking_segment('{"notes":["x"],"services":["123"'), 'inside')
        self.assertEqual(utils.ranking_segment('{"observations":[],"services":["123"],"reason":"x"'), 'after')

    def test_projection_preserves_bad_names_and_order(self):
        response=json.dumps({'notes':['x'],'services':['service 123','999','123','123','000'],
                             'reason':'observed','confidence':'low'})
        projected,audit=utils.project_ranking(response)
        self.assertEqual(json.loads(projected)['services'],json.loads(response)['services'])
        self.assertEqual(audit['host_truth_correction'],False)

    def test_extra_output_field_not_silently_removed(self):
        response='{"services":[],"reason":"x","confidence":"low","hidden_root":"123"}'
        self.assertEqual(utils.project_ranking(response)[0],response)

    def test_qa_na_separate_from_wrong_answer(self):
        truth={'answers':[None,{'value':'1.00','entity':'123','unit':'ms','statistic':'p95','phase':'current'}]}
        answer={'answers':[{'value':None,'entity':None,'unit':None,'statistic':None,'phase':None},
                           {'value':'1.005','entity':'service 123','unit':'ms','statistic':'p95','phase':'current'}]}
        result=utils.score_qa(json.dumps(answer),truth)
        self.assertEqual(result['applicable_questions'],1)
        self.assertEqual(result['standard'],0)
        self.assertEqual(result['tolerant'],1)

    def test_wrong_statistic_cannot_be_tolerated(self):
        truth={'answers':[{'value':'1','entity':'123','unit':'ms','statistic':'p95','phase':'current'}]}
        answer={'answers':[{**truth['answers'][0],'statistic':'p50'}]}
        result=utils.score_qa(json.dumps(answer),truth)
        self.assertFalse(result['questions'][0]['tolerant']['joint'])
        self.assertTrue(result['questions'][0]['tolerant']['components']['value'])

    def test_each_image_gather_preserves_text_and_positions(self):
        import torch
        ids=torch.tensor([10,99,99,11,99,99,99,12])
        pos=torch.arange(8).repeat(3,1)
        keep,actual,delta,original=utils.multimodal_gather(ids,pos,99,[2,3],[[1],[0,2]])
        self.assertEqual(keep,[0,2,3,4,6,7])
        self.assertTrue(torch.equal(actual,pos[:,keep]))
        self.assertEqual(delta,2)

    def test_gather_rejects_duplicate_and_wrong_image_counts(self):
        import torch
        ids=torch.tensor([10,99,99]);p=torch.arange(3).repeat(3,1)
        for counts,keep in [([3],[[1]]),([2],[[0,0]]),([2],[[2]])]:
            with self.assertRaises(ValueError):
                utils.multimodal_gather(ids,p,99,counts,keep)

    def test_position_exchange_is_whole_panel_and_semantic_exchange_all_labels(self):
        from PIL import Image
        from renderer.operations.source_workspace import qa_intervention
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'fixture.png'
            image=Image.new('RGB',(100,40),'black')
            image.paste('red',(0,0,40,40));image.paste('blue',(60,0,100,40));image.save(p)
            a={'card':'A','box':[0,0,40,40],'semantic':{'safe':True,'boxes':[[0,0,10,10],[0,20,10,10]]}}
            b={'card':'B','box':[60,0,40,40],'semantic':{'safe':True,'boxes':[[60,0,10,10],[60,20,10,10]]}}
            out=root/'swapped.png'
            a['semantic']['entity']='123';b['semantic']['entity']='456'
            a['local_fields']=[{'binding':'A.value','box':[10,10,5,5]}]
            b['local_fields']=[{'binding':'B.value','box':[70,10,5,5]}]
            geo={'panels':[a,b],'rows':[]}
            qa_intervention(p,geo,[a,b],'SEMANTIC',out)
            with Image.open(out) as im:
                self.assertEqual(im.getpixel((1,1)),(0,0,255))
                self.assertEqual(im.getpixel((1,21)),(0,0,255))
                self.assertEqual(im.getpixel((15,15)),(255,0,0))
            changed=qa_intervention(p,geo,[a,b],'POSITION',out)
            self.assertEqual(changed['geometry']['panels'][0]['local_fields'][0]['box'],[70,10,5,5])
            self.assertEqual(geo['panels'][0]['local_fields'][0]['box'],[10,10,5,5])
            with Image.open(out) as im:
                self.assertEqual(im.getpixel((15,15)),(0,0,255))


class DurableStages(unittest.TestCase):
    class Provider:
        def __init__(self):
            self.count=0;self.last_usage={'input_tokens':5,'output_tokens':4}
        def __call__(self,request):
            self.count+=1
            return '{"actions":[]}'

    def test_ledger_response_recovery_does_not_generate_again(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);provider=self.Provider()
            item={'key':'A__PLAN__BASE','id':'A','variant':'BASE','task':'ACTION','depends_on':None}
            def fault(stage):
                if stage=='after_ledger':
                    raise RuntimeError('simulated power loss')
            session=utils.RuntimeSession(root/'formal',provider,root)
            try:
                with self.assertRaises(RuntimeError):
                    session.run(item,fake_request(),lambda:{},fault=fault)
            finally:
                session.close()
            session=utils.RuntimeSession(root/'formal',provider,root)
            try:
                session.recover()
                record=session.run(item,fake_request(),lambda:{})
                self.assertEqual(record['status'],'complete')
                self.assertEqual(provider.count,1)
            finally:
                session.close()

    def test_shared_reference_and_true_repeat_different_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);provider=self.Provider()
            session=utils.RuntimeSession(root/'formal',provider,root)
            try:
                first={'key':'A','variant':'BASE','depends_on':None}
                session.run(first,fake_request(),lambda:{})
                shared=session.run({'key':'B','variant':'BASE','reference':'A'},fake_request(),lambda:{})
                self.assertEqual(shared['actual_calls'],0)
                with self.assertRaises(ValueError):
                    session.run({'key':'C','variant':'REPEAT','reference':'A'},fake_request(),lambda:{})
                session.run({'key':'D','variant':'REPEAT'},fake_request(),lambda:{})
                self.assertEqual(provider.count,2)
            finally:
                session.close()

    def test_committed_plan_survives_restart_before_final_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);provider=self.Provider()
            session=utils.RuntimeSession(root/'formal',provider,root)
            session.run({'key':'PLAN','variant':'BASE'},fake_request(),lambda:{})
            session.close()
            session=utils.RuntimeSession(root/'formal',provider,root)
            try:
                self.assertIsNotNone(session.completed('PLAN'))
                self.assertIsNone(session.completed('FINAL'))
                self.assertEqual(provider.count,1)
            finally:
                session.close()

    def test_duplicate_owner_rejected_and_pause_blocks_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);provider=self.Provider()
            session=utils.RuntimeSession(root/'formal',provider,root)
            try:
                with self.assertRaises(BlockingIOError):
                    utils.RuntimeSession(root/'formal',provider,root)
                utils.save(root/'formal/PAUSE',{})
                self.assertEqual(session.run({'key':'A','variant':'BASE'},fake_request(),lambda:{})['status'],'paused')
                self.assertEqual(provider.count,0)
            finally:
                session.close()


def run_tests():
    """Explicit CPU authority is required even for offline synthetic regressions."""
    from .gates import require_cpu,execution_fingerprint
    require_cpu()
    import os,io
    os.environ['CUDA_VISIBLE_DEVICES']=''
    utils.offline()
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c)
                             for c in (SourceContracts,OutputAndGeometry,DurableStages))
    stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    receipt={'status':'passed' if result.wasSuccessful() else 'failed',
             'execution_fingerprint':execution_fingerprint(),'tests':result.testsRun,
             'errors':len(result.errors),'failures':len(result.failures),'log':stream.getvalue(),
             'model_calls':0,'mode':'offline_model_substitute'}
    utils.save(utils.RESULTS/'qualification/unit.json',receipt)
    return receipt
