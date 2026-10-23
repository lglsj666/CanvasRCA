"""Independent numerical and operational CPU regressions; no model service."""
import unittest,math,tempfile
from pathlib import Path
from .utils import read,save,protocol,RESULTS,allocate_slots,farthest,fusion_plan,fuse_embeddings,redistribute,sink_candidates,score_qa,receive_qa,public_qa_items


class NumericalTests(unittest.TestCase):
    def test_exact_spatial(self):
        pool=list(range(25));anchors=[0,24];chosen=farthest(pool,anchors,5,10);reference=[]
        for _ in range(10):
            candidates=set(pool)-set(anchors)-set(reference)
            reference.append(min(candidates,key=lambda i:(-min((i%5-j%5)**2+(i//5-j//5)**2 for j in anchors+reference),i)))
        self.assertEqual(chosen,reference)

    def test_fusion_budget_and_values(self):
        import torch
        base={'anchors':[0,9],'evidence':list(range(1,9)),'q':4,'grid':[2,5],'image_tokens':10,'retained':[]}
        sig={str(i):['a' if i<5 else 'b'] for i in base['evidence']};features=torch.arange(30,dtype=torch.float32).reshape(10,3).to(torch.bfloat16)
        plans=[fusion_plan(base,sig,sig,a,'test') for a in ('F_SOURCE_MEAN','F_SOURCE_REP','F_SOURCE_SHAM')]
        self.assertEqual([g['representative'] for g in plans[0]['groups']],[g['representative'] for g in plans[2]['groups']])
        out=fuse_embeddings(features,plans[0])
        for g in plans[0]['groups']:
            expected=sum((features[i].float() for i in g['members']))/len(g['members'])
            self.assertTrue(torch.equal(out[plans[0]['retained'].index(g['representative'])],expected.to(torch.bfloat16)))
        self.assertTrue(torch.equal(out[0],features[0]));self.assertEqual(sum(allocate_slots([3,6,5],7)),7)
        with self.assertRaises(ValueError):allocate_slots([1]*5,4)

    def test_sink_mass_and_noop(self):
        import numpy as np,torch
        from .exps import torch_redistribute
        p=np.array([[.3,.1,.05,.05,.1,.2,.2],[.8,.01,.01,.01,.01,.01,.15]])
        image=[1,2,3,4,5];domain=[2,3];donors=[1];ordinary=[4,5];cfg=protocol()['sink_policy']
        for arm in protocol()['sink']:
            expected,audit=redistribute(p,image,domain,donors,arm,cfg,ordinary)
            actual,eligible,mass=torch_redistribute(torch.tensor(p)[:,None,:],image,domain,donors,arm,cfg,ordinary)
            np.testing.assert_allclose(actual[:,0].numpy(),expected,rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(expected.sum(-1),1);self.assertTrue((expected>=0).all())
        result,_=redistribute(p,image,domain,[],'S_EVID_REDIST',cfg,ordinary);np.testing.assert_array_equal(result,p)
        signals=np.ones((2,8,40))/40;signals[:,:,3]=.3;signals/=signals.sum(-1,keepdims=True)
        self.assertIn(3,sink_candidates(signals,list(range(40)),[0,1],cfg))
        self.assertNotIn(3,sink_candidates(signals,list(range(40)),[3],cfg))

    def test_receiver_prose_and_conflicts(self):
        q={'id':'q1','question':'Which statistic?','type':'string','mode':'single','solutions':[['p95']],
           'proof':{'display':'p95'},'support_cards':['C1'],'answer_vocabulary':{'p50':'p50','p95':'p95'}}
        self.assertEqual(score_qa('Q1: The statistic is p95.',[q])['conditional_credit'],1)
        self.assertEqual(score_qa('Q1: p50 or p95',[q])['conditional_credit'],0)
        self.assertEqual(score_qa('```json\n{"answers":[{"id":"q1","answer":"p95"},{"id":"q999","answer":"wrong"},]}\n```',[q])['conditional_credit'],1)
        with self.assertRaises(ValueError):receive_qa('q1: p95',[q])
        q2=dict(q,type='number',mode='required_values',solutions=[['0','2']],answer_vocabulary={})
        self.assertEqual(score_qa('{"q1":[0]}',[q2])['conditional_credit'],.5)
        self.assertEqual(score_qa('{"q1":[0,7]}',[q2])['conditional_credit'],0)
        self.assertEqual(score_qa('{"q1":[0,2]}',[q2])['conditional_credit'],1)
        self.assertEqual(score_qa('Q1: The value is 2 milliseconds.',[dict(q2,mode='single',solutions=[['2']],unit_factors={'milliseconds':1})])['conditional_credit'],1)

    def test_atomic_and_identity(self):
        from .utils import stable
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'complete.json';save(p,{'raw':'invalid response','state':'committed'})
            (Path(d)/'complete.json.interrupted.tmp').write_text('{')
            self.assertEqual(read(p)['raw'],'invalid response')
        self.assertNotEqual(stable({'op':'mean','pixels':'same'}),stable({'op':'gather','pixels':'same'}))

    def test_explicit_phase_comparison_prose(self):
        q={'id':'q1','question':'Which phase has the larger value?','type':'string','mode':'single',
           'solutions':[['current']],'proof':{'visible':'phase values'},'support_cards':['c'],
           'answer_vocabulary':{'reference':'reference','current':'current','equal':'equal','same':'equal'}}
        for answer in ('current is higher than reference','The current phase has a larger value than the reference phase.',
                       'reference is lower than current','current > reference'):
            self.assertEqual(score_qa('Q1: '+answer,[q])['conditional_credit'],1,answer)
        for answer in ('current or reference','current is not higher than reference',
                       'current is higher than reference, but reference is higher than current'):
            self.assertEqual(score_qa('Q1: '+answer,[q])['conditional_credit'],0,answer)
        equal=dict(q,solutions=[['equal']])
        self.assertEqual(score_qa('Q1: reference and current are equal.',[equal])['conditional_credit'],1)
        # Extraction must not change when the expected answer changes.
        from .utils import extract_answer_value,public_qa_items
        a=public_qa_items([q])[0];b=public_qa_items([dict(q,solutions=[['reference']])])[0]
        self.assertEqual(extract_answer_value('current is higher than reference',a),extract_answer_value('current is higher than reference',b))

    def test_empty_relationship_provenance(self):
        from .exps import source_units
        from .utils import stable
        inv={'cards':[{'card':'C1','index':1,'title':'candidate directory','modality':'G','protected':True,'entities':[]}]}
        empty={'source':'source-empty','path':'/data/edges','binding':None,
               'disposition':'empty_relation_no_panel','value_hash':stable([])}
        baseline=source_units(inv,[],{})
        self.assertEqual(source_units(inv,[empty],{}),baseline)
        for invalid in (dict(empty,value_hash=stable([['a','b']])),dict(empty,path='/title'),
                        dict(empty,disposition='unknown_hidden_fact')):
            with self.assertRaises(ValueError):source_units(inv,[invalid],{})

    def test_queue_excludes_stale_qa_files(self):
        from unittest.mock import patch
        from . import exps,utils
        row={'id':'inc','dataset':'dataset','event_group':'event'}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);results=root/'results';folder=results/'inputs/inc'
            save(folder/'U28.json',{});save(folder/'qa/U28.json',{'stale':True})
            save(folder/'qa/complete.json',{'status':'not_applicable','requests':{}})
            with patch.object(exps,'ROOT',root),patch.object(exps,'RESULTS',results),patch.object(exps,'ARMS',('U28',)),\
                 patch.object(exps,'protocol',lambda:{'qa_salt':'test','nominees':[]}),\
                 patch.object(utils,'roster',lambda:[row]),patch.object(utils,'subset',lambda rows,*args:rows):
                queue=exps.build_queue('formal')
                self.assertEqual([x['task'] for x in queue],['RCA'])
                save(folder/'qa/complete.json',{'status':'passed','requests':{'U28':'results/inputs/inc/qa/U28.json'}})
                queue=exps.build_queue('formal')
                self.assertEqual([x['task'] for x in queue],['RCA','QA'])

    def test_multimodal_positions(self):
        import torch
        from .utils import multimodal_gather
        ids=torch.tensor([1,99,99,99,2,99,99,3]);positions=torch.arange(8).repeat(3,1)
        keep,coords,delta,images=multimodal_gather(ids,positions,99,[3,2],[[0,2],[1]])
        self.assertEqual(keep,[0,1,3,4,6,7]);self.assertEqual(coords.tolist(),positions[:,keep].tolist())
        self.assertEqual(delta,2)

    def test_native_noop_gate_and_batch_isolation(self):
        import torch
        from types import SimpleNamespace
        from .exps import install_attention_layer
        torch.manual_seed(19)
        x=torch.randn(7,8,dtype=torch.float64);gate=torch.randn(7,4,dtype=torch.float64)
        records=[{'key':'a','start':0,'end':3,'prefill':True,'meta':{'length':3},'before':0},
                 {'key':'b','start':3,'end':7,'prefill':True,'meta':{'length':4},'before':0}]
        def project(qkv,positions):return qkv[:,:4],qkv[:,4:6],qkv[:,6:8],gate
        def attention(q,k,v):
            outputs=[]
            for r in records:
                sl=slice(r['start'],r['end']);qq=q[sl].reshape(-1,2,2).transpose(0,1)
                kk=k[sl].reshape(-1,1,2).transpose(0,1).repeat_interleave(2,0)
                vv=v[sl].reshape(-1,1,2).transpose(0,1).repeat_interleave(2,0)
                logits=(qq@kk.transpose(-1,-2))/math.sqrt(2)
                logits.masked_fill_(torch.triu(torch.ones(logits.shape[-2:],dtype=torch.bool),1),-torch.inf)
                outputs.append((torch.softmax(logits,-1)@vv).transpose(0,1).reshape(-1,4))
            return torch.cat(outputs)
        module=SimpleNamespace(qkv_proj=lambda h:(h,None),_project_qkv_gate=project,attn=attention,
          o_proj=lambda v:(v*2,None),num_heads=2,num_kv_heads=1,head_dim=2)
        state={'records':records,'requests':{r['key']:{'attention_region':None,'sink':None} for r in records}}
        expected=attention(*project(x,None)[:3])*torch.sigmoid(gate)*2
        install_attention_layer(state,module,3);out=torch.empty((7,4),dtype=torch.float64)
        module.forward(torch.arange(7),out,x);self.assertTrue(torch.equal(out,expected))
        altered=x.clone();altered[3:]+=100;other=out.clone();module.forward(torch.arange(7),other,altered)
        self.assertTrue(torch.equal(other[:3],out[:3]));self.assertFalse(torch.equal(other[3:],out[3:]))

    def test_commit_reference_repeat_and_resume(self):
        from unittest.mock import patch
        from . import utils
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);results=root/'results'
            item={'key':'x','id':'inc','task':'QA','force_call':False}
            req={'identity':'same','qa_items':[{'id':'q1','question':'Value?','type':'number','mode':'single','solutions':[['0']],
                'proof':{'visible':'0'},'support_cards':['c']}],'images':[],'retained_by_image':[]}
            with patch.object(utils,'ROOT',root),patch.object(utils,'RESULTS',results):
                r=utils.commit_call('formal',item,req,'q1: 0',{},1)
                again=utils.commit_call('formal',item,req,'q1: 0',{},99);self.assertEqual(r,again)
                with self.assertRaises(ValueError):utils.commit_call('formal',item,req,'q1: 1',{},2)
                known={};self.assertTrue(utils.remember_reference(known,'x',r))
                repeat=dict(r,item=dict(item,force_call=True));self.assertFalse(utils.remember_reference(known,'repeat',repeat))
                self.assertEqual(known,{'same':'x'})

    def test_passive_measurements_deferred_without_output_change(self):
        import torch
        from types import SimpleNamespace
        from .exps import install_attention_layer
        torch.manual_seed(49);x=torch.randn(5,8);gate=torch.randn(5,4)
        q=x[:,:4].reshape(5,2,2).transpose(0,1)
        k=x[:,4:6][None].expand(2,-1,-1);v=x[:,6:8][None].expand(2,-1,-1)
        logits=q@k.transpose(-1,-2)/math.sqrt(2)
        logits.masked_fill_(torch.triu(torch.ones(5,5,dtype=torch.bool),1),-torch.inf)
        probabilities=logits.softmax(-1);native=(probabilities@v).transpose(0,1).reshape(5,4)
        module=SimpleNamespace(qkv_proj=lambda h:(h,None),
            _project_qkv_gate=lambda h,p:(h[:,:4],h[:,4:6],h[:,6:8],gate),
            attn=lambda *args:native.clone(),o_proj=lambda a:(a,None),num_heads=2,num_kv_heads=1,head_dim=2)
        entry={'sink':None,'attention_region':{'names':['text','image'],'ids':[0,1,1,1,0]},
            'actual_selection':{'image_slots':[1,2,3],'domain_slots':[2]},'measurements':[],'measure_device':[],
            'query_indices':{'last_prompt':torch.tensor([4])},
            'region_layout':{'last_prompt':{'labels':torch.tensor([0,1,1,1,0]),'counts':[2,3]}}}
        state={'records':[{'key':'a','start':0,'end':5,'prefill':True,'meta':{'length':5},'before':0}],
            'requests':{'a':entry}}
        install_attention_layer(state,module,3);out=torch.empty_like(native);module.forward(None,out,x)
        torch.testing.assert_close(out,native*torch.sigmoid(gate),atol=0,rtol=0)
        expected=torch.stack((probabilities[:,-1,[0,4]].sum(-1).mean(),probabilities[:,-1,1:4].sum(-1).mean()))
        measured=entry['measure_device'][0]
        torch.testing.assert_close(measured['bins'],expected[None].expand(2,-1),atol=1e-7,rtol=1e-6)
        self.assertEqual(entry['measurements'],[]);self.assertEqual(measured['query'],'last_prompt')

    def test_qa_empty_oracle_and_invalid_ids(self):
        from .utils import validate_qa_item
        q={'id':'q1','question':'Entity?','type':'id','mode':'single','solutions':[['123']],
           'proof':{'visible':'123'},'support_cards':['c'],'id_domain':['123','456']}
        self.assertEqual(score_qa('{answers:[{id:"q1",answer:["123","999"]}]}',[q])['conditional_credit'],1.)
        self.assertEqual(score_qa('{"q1":["123","456"]}',[q])['conditional_credit'],0.)
        for oracle in ([],[[]],[[None]],[['']]):
            with self.assertRaises(ValueError):validate_qa_item(dict(q,solutions=oracle))

    def test_cross_runtime_reference_is_not_reused(self):
        from .main import current_runtime_reference
        from .utils import stable
        r={'generation_identity':'input','item':{'force_call':False},'usage':{'runtime_revision':'old'},'status':'complete','raw':'retained answer'}
        known={};self.assertFalse(current_runtime_reference(known,'old',r));self.assertEqual(known,{})
        r['usage']={'runtime_revision':'rq49_fused_sink_v3','implementation_generation_identity':stable(['input','rq49_fused_sink_v3'])}
        self.assertTrue(current_runtime_reference(known,'new',r));self.assertEqual(known,{'input':'new'})
        r['item']['force_call']=True;self.assertFalse(current_runtime_reference({},'repeat',r))
        r['usage']['implementation_generation_identity']='wrong';self.assertFalse(current_runtime_reference({},'bad',r))

    def test_resume_review_proof_preserves_original(self):
        from unittest.mock import patch
        from . import gates
        from .utils import digest
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);path=root/'old/review.json';save(path,{'status':'passed','fingerprint':'old'})
            hashes={}
            for n in ('review','timing_review','attention_review','response_review'):
                relative='smoke_performance_v5/'+n+'.json';save(root/relative,{'status':'passed'});hashes[relative]=digest(root/relative)
            proof={'status':'passed','fingerprint':'new','review_hashes':{'old':digest(path)},'supporting_receipts':hashes}
            with patch.object(gates,'RESULTS',root):
                with self.assertRaises(RuntimeError):gates.require_smoke_review('old','new')
                gates.require_smoke_review('old','new',proof)
                self.assertEqual(read(path)['fingerprint'],'old')
                save(root/'smoke_performance_v5/attention_review.json',{'status':'failed'})
                with self.assertRaises(RuntimeError):gates.require_smoke_review('old','new',proof)

    def test_primitive_shape_support_budget(self):
        from .utils import shape_plan
        base={'anchors':[0],'evidence':list(range(1,10)),'q':5,'grid':[2,5],'image_tokens':10,'retained':[0,2,4,6,8,9]}
        p=shape_plan(base,[{'kind':'line','points':[[0,0],[1,10],[2,0]],'support':[[1],[2],[3]],'source':'line1'}])
        self.assertEqual(len(p['retained']),6);self.assertIn(0,p['retained']);self.assertTrue(set(p['retained'])<=set(range(10)))

    def test_metric_only_qa_is_answerable(self):
        import json
        from .exps import qa_metric_targets
        card={'id':'MET001','kind':'metric','title':'MET01 · usage','entity':'123','unit':'ratio_or_percent',
              'data':{'details':[{'name':'baseline','value':'0'},{'name':'peak','value':'2.50'}]}}
        items,target=qa_metric_targets({'id':'example'},{'evidence':{'cards':[card]}},{'candidates':['123','456']})
        self.assertEqual(len(items),4);self.assertTrue(target['metric_only'])
        self.assertNotIn('123',items[1]['question'])
        answers={'q1':'0','q2':'123','q3':'ratio or percent','q4':'peak is higher than baseline'}
        self.assertEqual(score_qa(json.dumps(answers),items)['conditional_credit'],1.)
        answers['q3']='ms or ratio or percent'
        self.assertEqual(score_qa(json.dumps(answers),items)['conditional_credit'],.75)
        self.assertEqual(items[0]['solutions'],[['0']])

    def test_worker_rpc_packet_decodes_before_gather(self):
        import torch
        from .exps import decode_operator_packet
        from .utils import vllm_tensor_wire
        tensors={'input_ids':torch.tensor([[1,2,3]]),'pixel_values':torch.arange(12,dtype=torch.float32).reshape(2,6)}
        wire={'batch':{k:vllm_tensor_wire(v) for k,v in tensors.items()},'keep':[0,2]}
        packet=decode_operator_packet(wire)
        self.assertEqual(packet['batch']['input_ids'][0,packet['keep']].tolist(),[1,3])
        for k,v in tensors.items():self.assertTrue(torch.equal(v,packet['batch'][k]))
        self.assertIsInstance(wire['batch']['input_ids'],dict)

    def test_truncated_qa_question_sections(self):
        items=[{'id':'q1','question':'What value?','type':'number','mode':'single','solutions':[['0']],
                'proof':{'visible':'0'},'support_cards':['c']},
               {'id':'q2','question':'What entity?','type':'id','mode':'single','solutions':[['123']],
                'proof':{'visible':'123'},'support_cards':['c'],'id_domain':['123','456']}]
        raw='1. **q1: What value?**\n* I considered 42.\n* Answer: 0\n2. **q2: What entity?**\n* Answer: 123\nThe response ends here'
        self.assertEqual(score_qa(raw,items)['conditional_credit'],1.)
        self.assertEqual(score_qa(raw+'\n* Answer: 456',items)['conditional_credit'],.5)
        self.assertEqual(score_qa(raw+'\nq1: 42',items)['conditional_credit'],.5)
        headings='1. **Question q1: What value?**\n* Maybe 0 or 42.\n2. **q2: What entity?**\n* It could be 123.'
        score=score_qa(headings,items)
        self.assertEqual(score['conditional_credit'],0.)
        self.assertEqual(score['reception']['answers'],{})


class RetentionTests(unittest.TestCase):
    """Isolated storage fixtures; no renderer, processor or model calls."""
    def fixture(self,project,reference=False):
        import hashlib
        base=project/'results';objects=base/'objects';objects.mkdir(parents=True)
        def obj(data,suffix):
            path=objects/(hashlib.sha256(data).hexdigest()+suffix);path.write_bytes(data);return path
        image=obj(b'original model-visible PNG bytes','.png')
        request={'prompt':'exact instructions\nincident evidence','messages':[{'role':'user','content':'exact instructions'}],
            'identity':'generation','images':[str(image.relative_to(project))],'image_sha256':[image.stem]}
        import json
        path=obj(json.dumps(request).encode(),'.json')
        record={'request_path':str(path.relative_to(project)),'request_sha256':path.stem,'raw':'invalid original answer retained',
            'generation_identity':'generation','reference':None,'scores':{'mrr':0},
            'usage':{'attention_requested':True,'attention_record_key':'call'},
            'item':{'key':'call','arm':'U28','dataset':'dataset','task':'RCA','request_path':'results/inputs/incident/U28.json'}}
        save(base/'formal/completed/call.json',record)
        save(base/'formal/attention/call.json',{'layers':[3,23,43,63],'mass':[.2,.8],'query':'last_prompt'})
        if reference:
            other=dict(record,reference='call',item=dict(record['item'],key='reference'))
            save(base/'formal/completed/reference.json',other)
        save(base/'formal/phase_complete.json',{'status':'complete','positions':1+int(reference),'expected':1+int(reference),'fingerprint':'original'})
        save(base/'inputs/incident/U28.json',request)
        save(base/'inputs/incident/packet.json',{'facts':['0','1.00',None],'provenance':['original record']})
        save(base/'inputs/incident/images.json',{'U28':{'path':str(image.relative_to(project)),'sha256':image.stem,
            'support':{'roles':{'source': [1,2]}},'provenance':{'original':'source'},'preparation_timing':{'seconds':1},
            'operator':{'retained':[0,1,2]},'retained':[0,1,2]}})
        (base/'cache').mkdir();(base/'cache/unused.bin').write_bytes(b'cache'*100)
        bad=base/'smoke_performance_v4/cpu_stacks.json';bad.parent.mkdir();bad.write_bytes(b'not UTF-8 \xfd')
        orphan=obj(b'<html>unused render, not a model input</html>','.html')
        save(base/'frozen/source/old/source.py.json',{'source':'unchanged'})
        save(base/'frozen/source/new/source.py.json',{'source':'unchanged'})
        return base,path,image,orphan

    def test_cleanup_preserves_complete_conversations_and_measurements(self):
        from .gates import finalize_retention
        from .utils import digest
        with tempfile.TemporaryDirectory() as d:
            project=Path(d);base,req,image,orphan=self.fixture(project,reference=True)
            targets=[req,image,base/'formal/completed/call.json',base/'formal/attention/call.json']
            hashes=[digest(p) for p in targets];packet=read(base/'inputs/incident/packet.json')
            (base/'inputs/incident/U28.json.123.456.tmp').write_bytes(b'interrupted unsubmitted preparation')
            plan=finalize_retention(base,project,apply=False)
            self.assertEqual(plan['status'],'verified_not_deleted');self.assertTrue((base/'cache').exists())
            report=finalize_retention(base,project)
            self.assertEqual(report['status'],'passed');self.assertEqual(report['completed_actual_calls'],1)
            self.assertEqual(report['retained_conversations'],2)
            self.assertEqual(hashes,[digest(p) for p in targets]);self.assertFalse(orphan.exists())
            self.assertFalse((base/'cache').exists());self.assertFalse((base/'inputs').exists())
            self.assertFalse((base/'smoke_performance_v4/cpu_stacks.json').exists())
            self.assertEqual(read(base/'audits/cases/incident/packet.json'),packet)
            support=read(base/'audits/image_support.json')['views']['incident/U28']['support']
            self.assertEqual(read(project/support['path']),{'roles':{'source':[1,2]}})
            manifest=read(base/'retained_manifest.json')
            for name,entry in manifest['files'].items():self.assertEqual(digest(base/name),entry['sha256'])
            self.assertEqual(finalize_retention(base,project),report)
            self.assertTrue((base/'frozen/source/old/source.py.json').samefile(base/'frozen/source/new/source.py.json'))
            index=read(base/'conversations/index.json');self.assertEqual(len(index['records']),2)
            self.assertNotIn('invalid original answer retained',(base/'conversations/index.html').read_text())

    def test_required_corruption_blocks_before_deletion(self):
        from .gates import finalize_retention
        from .utils import digest
        for defect in ('image_hash','missing_attention','broken_reference','invalid_input_json','phase_count','escaping_input'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as d:
                project=Path(d);base,req,image,_=self.fixture(project)
                recordpath=base/'formal/completed/call.json';record=read(recordpath)
                if defect=='image_hash':image.write_bytes(b'changed PNG')
                elif defect=='missing_attention':(base/'formal/attention/call.json').unlink()
                elif defect=='broken_reference':record['reference']='missing';save(recordpath,record)
                elif defect=='invalid_input_json':
                    req.write_bytes(b'\xfd');record['request_sha256']=digest(req);save(recordpath,record)
                elif defect=='escaping_input':
                    outside=project/'outside.json';outside.write_bytes(req.read_bytes())
                    record['request_path']='outside.json';save(recordpath,record)
                else:save(base/'formal/phase_complete.json',{'status':'complete','positions':2})
                with self.assertRaises((ValueError,UnicodeError)):finalize_retention(base,project)
                self.assertTrue((base/'cache/unused.bin').exists());self.assertTrue((base/'inputs/incident/U28.json').exists())

    def test_partial_answer_and_nested_retention_json_are_preserved(self):
        from .gates import finalize_retention
        with tempfile.TemporaryDirectory() as d:
            project=Path(d);base,*_=self.fixture(project)
            save(base/'formal/partial/unique.json',{'identity':'other','raw':'unique interrupted response'})
            save(base/'formal/partial/duplicate.json',{'identity':'generation','raw':'invalid original answer retained'})
            save(base/'audits/retention.json',{'unique_evidence':'nested metadata'})
            finalize_retention(base,project)
            self.assertTrue((base/'formal/partial/unique.json').exists())
            self.assertFalse((base/'formal/partial/duplicate.json').exists())
            self.assertIn('audits/retention.json',read(base/'retained_manifest.json')['files'])

    def test_distinct_prepared_and_actual_attention_selections_are_both_preserved(self):
        import json,hashlib
        from .gates import finalize_retention
        with tempfile.TemporaryDirectory() as d:
            project=Path(d);base,path,*_=self.fixture(project);req=read(path)
            req['retained_by_image']=[[0,2]]
            req['operators']=[{'anchors':[0],'evidence':[1,2],'retained':[0,1]}]
            content=json.dumps(req).encode();target=path.parent/(hashlib.sha256(content).hexdigest()+'.json');target.write_bytes(content)
            p=base/'formal/completed/call.json';record=read(p)
            record.update(request_path=str(target.relative_to(project)),request_sha256=target.stem)
            record['usage']['actual_selection']={'retained_by_image':[[0,2]]};save(p,record)
            finalize_retention(base,project)
            account=read(base/'audits/attention_retention_accounting.json')
            self.assertEqual(account['distinct_selection_variants_charged_separately'],1)
            self.assertEqual(read(target)['operators'][0]['retained'],[0,1])
            self.assertEqual(read(p)['usage']['actual_selection']['retained_by_image'],[[0,2]])


def run():
    import os
    os.environ['CUDA_VISIBLE_DEVICES']=''
    from .utils import offline
    offline()
    from .gates import require_check,execution_fingerprint
    require_check('static')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NumericalTests))
    report={'status':'passed' if result.wasSuccessful() else 'blocked','fingerprint':execution_fingerprint(),
        'tests':result.testsRun,'failures':[(str(a),b) for a,b in result.failures+result.errors],
        'new_model_calls':0,'scope':'independent numerics, oracle-blind receiver, atomic commits, positional transport'}
    save(RESULTS/'qualification/unit.json',report)
    # Runtime-specific full input checks remain separate; this is not a GPU certificate.
    return report
