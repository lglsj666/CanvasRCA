"""Future CPU regressions. Authored for this delivery; NOT executed by static."""
import unittest
import tempfile
import json
import math
from pathlib import Path
from . import exps
from .utils import RuntimeSession,save,stable,score_qa


class SelectionTests(unittest.TestCase):
    def test_source_uniform_anchor_does_not_replace_graphic(self):
        groups={'a':[1,2,3],'b':[21,22,23]}
        keep,reasons=exps.source_uniform(groups,10,2)
        self.assertEqual(keep,[2,22]);self.assertEqual([r['selected_for'] for r in reasons],['a','b'])

    def test_shared_token_credits_all_true_sources_once(self):
        keep,reasons=exps.source_uniform({'a':[1],'b':[1,2]},10,1)
        self.assertEqual(keep,[1]);self.assertEqual(reasons[0]['credited_sources'],['a','b'])

    def test_group_order_is_not_entity_sort(self):
        first=exps.source_uniform({'obs2':[11,12],'obs1':[1,2]},5,3)
        second=exps.source_uniform({'obs1':[1,2],'obs2':[11,12]},5,3)
        self.assertEqual(first,second);self.assertEqual(len(first[0]),3)

    def test_independent_spatial_farthest_oracle(self):
        pool=list(range(20));selected=[0,19];want=[]
        for _ in range(6):
            score={p:min(math.hypot(p%5-s%5,p//5-s//5) for s in selected) for p in pool if p not in selected}
            token=min(score,key=lambda p:(-score[p],p));selected.append(token);want.append(token)
        self.assertEqual(exps.farthest(pool,[0,19],5,6),want)

    def test_exact_three_retention_budgets(self):
        support={'anchors':[0,5],'roles':{'r':{'tokens':[1,2,6,7]}},'image_tokens':12,'grid':[3,4]}
        prov={'roles':[{'id':'r','source_occurrence':'a1/values_codec'}]};u=[0,1,5,7]
        plans={a:exps.selection_plan(a,support,prov,u,{'c':list(range(12))}) for a in exps.ARMS[3:]}
        self.assertEqual(len(plans['V_SOURCE_UNIFORM']['retained']),len(u))
        self.assertEqual(len(plans['V_DOMAIN_FULL']['retained']),6)
        self.assertEqual(len(plans['V_CONTEXT_FILL']['retained']),6)
        self.assertTrue(set(u)<=set(plans['V_CONTEXT_FILL']['retained']))
        for p in plans.values():self.assertTrue({0,5}<=set(p['retained']))

    def test_context_cannot_cross_card_boundary_or_wrap_row(self):
        support={'anchors':[0],'roles':{'r':{'tokens':[3,7]}},'image_tokens':12,'grid':[3,4]}
        p=exps.selection_plan('V_CONTEXT_FILL',support,{'roles':[{'id':'r','source_occurrence':'a/values'}]},[0,3],{'one':[0,1,2,3,4,5,6,7],'other':[8,9,10,11]})
        self.assertNotIn(8,p['retained']);self.assertNotIn(4,[r['token'] for r in p['selection_reasons'] if r['reason']=='local_context'])

    def test_empty_optional_set(self):
        self.assertEqual(exps.source_uniform({},4,0),([],[]))

    def test_invalid_historical_selection_rejects(self):
        s={'anchors':[0],'roles':{'r':{'tokens':[1,2]}},'image_tokens':4,'grid':[1,4]}
        with self.assertRaises(ValueError):exps.selection_plan('V_SOURCE_UNIFORM',s,{'roles':[{'id':'r','source_occurrence':'a/v'}]},[0,3],{})


class OwnershipTests(unittest.TestCase):
    def fixture(self):
        atoms=[{'id':'a0','kind':'literal','raw':'Observed request pairs:\n[]','value_wire':None,'part':0,'prefix':''},
            {'id':'a1','kind':'literal','raw':'Continuous pair fields:\n[]','value_wire':None,'part':1,'prefix':''},
            {'id':'a2','kind':'json','raw':'{"from":"123","to":"456","relation":"calls"}\n','value_wire':'{"from":"123","to":"456","relation":"calls"}','part':2,'prefix':''},
            {'id':'a3','kind':'window','raw':'MET01 | 123 | signal | ms\nfirst=0,last=1\n','value_wire':None,'part':3,'prefix':''}]
        parts=[{'type':'text','text':a['raw']} for a in atoms]
        return {'organization':{'schema':'FullEvidenceOrganizationPacketV1','atoms':atoms,'neutral_edits':{},
            'sections':[{'part':i,'atoms':[a['id']]} for i,a in enumerate(atoms)]},'payload':{'relations':[{'id':'PAIR01'}]},'texts':{'RAW_TEXT':parts},'candidates':['123','456']}

    def test_pair_samples_and_statistics_move_together(self):
        p=self.fixture();packet=exps.ownership(p,'H_MARGINAL');rows={r['occurrence']:r for r in packet['records']}
        self.assertEqual(rows['a0']['owner'],'image');self.assertEqual(rows['a1']['owner'],'image');self.assertEqual(rows['a2']['owner'],'text')
        text=exps.residual_text(p,packet);self.assertEqual(text,p['texts']['RAW_TEXT'][2:])

    def test_topology_removes_only_exact_sources(self):
        p=self.fixture();packet=exps.ownership(p,'H_TOPOLOGY');result=exps.residual_text(p,packet)
        self.assertEqual(result,[p['texts']['RAW_TEXT'][i] for i in (0,1,3)])

    def test_same_entity_is_not_same_fact(self):
        p=self.fixture();packet=exps.ownership(p,'H_TOPOLOGY');self.assertEqual(packet['records'][3]['owner'],'text')

    def test_missing_pair_fallback_is_exact_topology(self):
        p=self.fixture();p['payload']['relations']=[]
        for arm in ('H_MARGINAL','H_TOPO_MARGINAL'):
            packet=exps.ownership(p,arm);self.assertTrue(packet['fallback']);self.assertEqual(packet['effective_arm'],'H_TOPOLOGY')
            self.assertEqual(exps.residual_text(p,packet),exps.residual_text(p,exps.ownership(p,'H_TOPOLOGY')))

    def test_closure_split_and_duplicate_ids_fail(self):
        p=self.fixture();packet=exps.ownership(p,'H_MARGINAL');packet['records'][1]['owner']='text'
        with self.assertRaises(ValueError):exps.audit_ownership(packet)
        p['organization']['atoms'].append(p['organization']['atoms'][0])
        with self.assertRaises(ValueError):exps.ownership(p,'H_MARGINAL')

    def test_lexical_zero_extreme_and_escaped_strings(self):
        raw='{"zero":0.0000,"large":1.2500e+100,"escaped":"x\\ny","none":null}'
        self.assertEqual(exps.wire(exps.lexload(raw)),raw)
        with self.assertRaises(ValueError):exps.lexload('{"a":1,"a":2}')

    def test_instruction_consolidation_preserves_diagnostic_text(self):
        p=self.fixture()
        for raw,kind in [('Source reading: task-only rules.','literal'),('LOG01 | observed template: Source reading: 0.0000','literal')]:
            i=len(p['texts']['RAW_TEXT']);aid='added'+str(i)
            p['texts']['RAW_TEXT'].append({'type':'text','text':raw})
            p['organization']['atoms'].append({'id':aid,'kind':kind,'raw':raw,'value_wire':None,'part':i,'prefix':''})
            p['organization']['sections'].append({'part':i,'atoms':[aid]})
        packet=exps.ownership(p,'H_TOPOLOGY')
        old=exps.residual_text(p,packet);new=exps.residual_text(p,packet,strip_instructions=True)
        self.assertEqual(new,[r for r in old if r['text']!='Source reading: task-only rules.'])
        self.assertTrue(any('0.0000' in r['text'] for r in new))

    def test_instruction_section_cannot_hide_a_diagnostic_record(self):
        p=self.fixture();p['organization']['atoms'][3]['raw']='Source reading: MET01 | 0.0000'
        p['texts']['RAW_TEXT'][3]['text']=p['organization']['atoms'][3]['raw']
        with self.assertRaises(ValueError):exps.residual_text(p,exps.ownership(p,'H_TOPOLOGY'),strip_instructions=True)

    def test_unknown_graph_shape_fails(self):
        p=self.fixture();p['organization']['atoms'][2]['value_wire']='{"from":"123","to":"456","relation":"private_unknown"}'
        with self.assertRaises(ValueError):exps.topology_cards(p)

    def test_operation_bound_parent_child_preserves_directions_and_operation(self):
        p=self.fixture();value={'parent':['123','parent/op'],'child':['456','child/op'],
            'relation':'observed parent span -> child span','supporting_span_pairs':12}
        p['organization']['atoms'][2]['value_wire']=json.dumps(value)
        cards,bindings=exps.topology_cards(p)
        edge=cards[0]['data']['edges'][0]
        self.assertEqual((edge['source'],edge['target'],edge['kind']),('123','456','request_parent'))
        values=[d['value'] for c in cards if c['kind']=='inventory' for d in c['data']['details']]
        self.assertEqual(values,['parent/op','child/op','12'])

    def test_pair_canvas_uses_parallel_phase_rows_not_both_added(self):
        card={'id':'PAIR01','kind':'trace_joint','data':{'parent_operation':'p','child_operation':'c',
            'samples':[{'phase':phase} for phase in ('reference','current') for _ in range(32)]}}
        design=exps.hybrid_design([card]);self.assertLess(design['viewport']['height'],2304)


class SmokeBudgetTests(unittest.TestCase):
    def review_at(self,seconds,clock_seconds=900):
        from unittest.mock import patch
        from . import gates
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            save(root/'frozen/smoke_queue.json',[])
            save(root/'smoke/logical_clock.json',{'started_unix':1000,'deadline_unix':1000+clock_seconds})
            save(root/'smoke/summary.json',{'status':'passed','seconds':seconds})
            save(root/'smoke/phase_complete.json',{'status':'complete'})
            with patch.object(gates,'RESULTS',root),patch.object(gates,'require_execution'),patch.object(gates,'execution_fingerprint',return_value='offline'):
                return gates.review_smoke()

    def test_full_registered_window_is_accepted(self):
        self.assertEqual(self.review_at(899)['status'],'passed')

    def test_overrun_is_rejected(self):
        self.assertEqual(self.review_at(901)['status'],'failed')

    def test_old_shorter_clock_cannot_qualify_new_round(self):
        self.assertEqual(self.review_at(500,clock_seconds=300)['status'],'failed')


class RuntimeTests(unittest.TestCase):
    def test_serial_ledger_eight_writers_and_durable_reopen(self):
        from concurrent.futures import ThreadPoolExecutor
        from .utils import serialized_call_register
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'calls.sqlite';ledger=serialized_call_register(path,32,'offline',18)
            def transaction(i):
                attempt,_=ledger.begin(str(i),str(i),'QA')
                ledger.finish(attempt,{'output':i});return attempt
            with ThreadPoolExecutor(max_workers=8) as pool:ids=list(pool.map(transaction,range(18)))
            self.assertEqual(len(set(ids)),18);self.assertEqual(ledger.summary(),{'complete':18})
            self.assertEqual(ledger.db.execute('PRAGMA journal_mode').fetchone()[0],'delete')
            self.assertEqual(ledger.db.execute('PRAGMA synchronous').fetchone()[0],2)
            with self.assertRaises(RuntimeError):ledger.begin('overflow','overflow','QA')
            ledger.close();ledger=serialized_call_register(path,32,'offline',18)
            try:self.assertEqual(ledger.summary(),{'complete':18});self.assertEqual(ledger.cached('0','0','QA'),{'output':0})
            finally:ledger.close()

    def test_ledger_owner_excludes_other_run_folders(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);one=RuntimeSession(root/'one',ledger_folder=root)
            try:
                with self.assertRaises(BlockingIOError):RuntimeSession(root/'two',ledger_folder=root)
            finally:one.close()

    def test_cpu_preparation_interleaves_registered_sources(self):
        from RQs.RQ4_1.src.utils import source_order
        rows=[{'dataset':ds,'source':str(s),'id':(ds,s,i)} for ds in ('aiops2022','aiops2025') for s in range(4) for i in range(2)]
        ordered=source_order(rows)
        self.assertEqual(len({(r['dataset'],r['source']) for r in ordered[:8]}),8)
        self.assertEqual({r['id'] for r in ordered},{r['id'] for r in rows})

    def test_power_loss_commit_reference_repeat_pause(self):
        class OfflineProvider:
            calls=0;last_usage={'input_tokens':10,'output_tokens':3}
            def __call__(self,request):
                self.calls+=1;return json.dumps({f'q{i}':None for i in range(1,7)})
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);provider=OfflineProvider();request={'identity':stable('offline'),'task':'QA'}
            expected={f'q{i}':None for i in range(1,7)};item={'key':'one','variant':'BASE'}
            session=RuntimeSession(root/'run',provider,ledger_folder=root)
            def crash(stage):
                if stage=='after_response':raise RuntimeError('simulated power loss')
            with self.assertRaises(RuntimeError):session.run(item,request,lambda:expected,crash)
            session.close();session=RuntimeSession(root/'run',provider,ledger_folder=root);session.recover()
            session.run(item,request,lambda:expected);self.assertEqual(provider.calls,1)
            session.run(item,request,lambda:expected);self.assertEqual(provider.calls,1)
            ref=session.run({'key':'ref','variant':'BASE','reference':'one'},request,lambda:expected);self.assertEqual(ref['actual_calls'],0)
            with self.assertRaises(ValueError):session.run({'key':'bad','variant':'REPEAT','reference':'one'},request,lambda:expected)
            session.run({'key':'repeat','variant':'REPEAT'},request,lambda:expected);self.assertEqual(provider.calls,2)
            save(root/'run/PAUSE',{'pause':True});self.assertEqual(session.run({'key':'paused','variant':'BASE'},request,lambda:expected)['status'],'paused')
            session.close()

    def test_duplicate_owner_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            one=RuntimeSession(Path(folder)/'run',ledger_folder=folder)
            try:
                with self.assertRaises(BlockingIOError):RuntimeSession(Path(folder)/'run',ledger_folder=folder)
            finally:one.close()

    def test_tolerant_qa_does_not_change_entity_or_decimal(self):
        expected={f'q{i}':None for i in range(1,7)};expected['q1']={'entity':'123','unit':'ms','value':'0.1000'}
        answer=dict(expected);answer['q1']={'entity':'service 123','unit':'ms','value':'1e-1 ms'}
        score=score_qa(json.dumps(answer),expected);self.assertEqual(score['standard'],0);self.assertEqual(score['tolerant'],1)
        answer['q1']['entity']='124';self.assertEqual(score_qa(json.dumps(answer),expected)['tolerant'],0)

    def test_multimodal_gather_preserves_text_and_positions(self):
        import torch
        from .utils import multimodal_gather
        ids=torch.tensor([5,99,99,6,99,99,7]);positions=torch.arange(7).repeat(3,1)
        keep,coords,delta,images=multimodal_gather(ids,positions,99,[2,2],[[1],[0]])
        self.assertEqual(keep,[0,2,3,4,6]);self.assertEqual(coords[0].tolist(),keep);self.assertEqual(delta,2)

    def test_attention_storage_budget(self):
        from vlmrca.vlm.passive_summary import AttentionStore
        self.assertLessEqual(AttentionStore.storage_ceiling(10000),1000000000)

    def test_attention_distinguishes_every_image_header_and_preserves_text(self):
        from copy import deepcopy
        from .utils import attention_regions
        request={'hybrid':True,'grid_thw':[[1,8,4]]*2,'geometry':[
            {'width':64,'height':128,'panels':[{'card':'p'+str(i),'box':[0,86,64,42]}]} for i in range(2)]}
        before=deepcopy(request);images=list(range(8))+list(range(9,17))
        result=attention_regions(request,[8,8],images,list(range(17)),17)
        self.assertEqual(request,before)
        for i in range(2):
            self.assertEqual(result['ids'].count(result['names'].index(f'image:{i}:header')),6)
            self.assertEqual(result['ids'].count(result['names'].index(f'image:{i}:panel:p{i}')),2)
        self.assertEqual(result['ids'][8],1)

    def test_attention_empty_transfer_is_text_only(self):
        from .utils import attention_regions
        result=attention_regions({'hybrid':True,'grid_thw':[],'geometry':[]},[],[],[0,2],3)
        self.assertEqual(result,{'ids':[1,1],'names':['other:generated','text:instructions_and_evidence']})


def run_tests():
    import io
    from .gates import require_cpu
    require_cpu()
    suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__,fromlist=['*']))
    buffer=io.StringIO();result=unittest.TextTestRunner(stream=buffer,verbosity=2).run(suite)
    return {'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,
        'failures':len(result.failures),'errors':len(result.errors),'log':buffer.getvalue(),'new_model_calls':0}


def check_visual_determinism():
    """Actual unified-renderer repaint, independently compared with qualified PNG."""
    from .utils import RESULTS,read,digest,offline
    from .gates import require_cpu,execution_fingerprint
    from renderer.main import render
    require_cpu();offline()
    original=read(RESULTS/'inputs/INC-D28AC6CAEFE4/source.json')['hybrid_images']['pair'][1]
    folder=RESULTS/'cache/determinism'/execution_fingerprint()
    save(folder/'evidence.json',original['evidence']);save(folder/'design.json',original['design'])
    target=folder/'render'
    if not target.exists():render(folder/'evidence.json',folder/'design.json',target)
    manifest=read(target/'manifest.json');sha=digest(target/'dashboard.png')
    if manifest['status']!='passed' or sha!=original['sha256']:raise ValueError('Deterministic redraw differs from qualified pixels')
    result={'status':'passed','execution_fingerprint':execution_fingerprint(),'sha256':sha,
        'case':'INC-D28AC6CAEFE4','card':'PAIR02','scope':'actual long-operation/extreme-duration source-complete repaint','new_model_calls':0}
    save(RESULTS/'qualification/determinism.json',result);return result


def check_transport_invariance():
    """Actual CPU packets: corrected passive maps never change model inputs."""
    import importlib.util,torch
    from transformers import AutoProcessor
    from . import utils
    from .utils import RESULTS,MODEL,read,digest,offline
    from .gates import require_cpu,execution_fingerprint
    require_cpu();offline()
    request=read(RESULTS/'mechanism/INC-D9245047C658/requests.json')['H_TOPO_MARGINAL']
    processor=AutoProcessor.from_pretrained(MODEL,local_files_only=True)
    current=utils.vllm_prompt_packet(request,processor)
    a=current['metadata']['attention']
    for i in range(len(request['images'])):
        if f'image:{i}:header' not in a['names']:raise ValueError('Image header is not represented in attention regions')
    old=RESULTS/'qualification/history_v3/source/utils.py';compared=False
    if old.exists():
        snapshot=read(old.parent.parent/'source_snapshot.json')
        if digest(old)!=snapshot['utils_sha256']:raise ValueError('Qualification reference changed')
        spec=importlib.util.spec_from_file_location('RQs.RQ4_5.src._cpu_reference_utils',old)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for name in ('ROOT','RQ','RESULTS','SOURCE_ROOT','MODEL','HISTORY'):setattr(module,name,getattr(utils,name))
        previous=module.vllm_prompt_packet(request,processor)
        for k,v in previous['batch'].items():
            if not torch.equal(v,current['batch'][k]):raise ValueError('Model processor tensor changed: '+k)
        for key in ('keep','source_by_slot','token_ids','image_positions','image_tokens_original'):
            if previous[key]!=current[key]:raise ValueError('Model gather/sequence changed: '+key)
        for key in previous['metadata']:
            if key!='attention' and previous['metadata'][key]!=current['metadata'][key]:raise ValueError('Position/model metadata changed: '+key)
        if previous['metadata']['attention']==a:raise ValueError('Registered multi-image region intervention did not change attribution')
        compared=True
    result={'status':'passed','execution_fingerprint':execution_fingerprint(),'legacy_comparison':compared,
        'scope':'actual CPU pixel/input tensors, gather, token IDs and MRoPE; only passive attention-region attribution may differ',
        'images':len(request['images']),'headers':sum(':header' in n for n in a['names']),'new_model_calls':0}
    save(RESULTS/'qualification/transport_audit.json',result);return result
