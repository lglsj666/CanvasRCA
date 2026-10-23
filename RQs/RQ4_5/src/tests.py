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


def chunked_capture_regression():
    """Affected CPU-only regression; no model weights, processor or renderer."""
    import torch
    from types import SimpleNamespace
    from .exps import VLLMWorkerExtension
    class Tap:
        def __init__(self):self.active={'seen':0};self.observed=[]
        def observe(self,module,q,k,mask,scale):
            self.observed.append((q[...,-1:,:].clone(),k.clone()))
            self.active['seen']+=1
    torch.manual_seed(4511);q=torch.randn(1,4,13,8);k=torch.randn(1,2,13,8)
    tap=Tap();entry={'tap':tap,'attention_module':SimpleNamespace(layer_idx=3)}
    before=0
    for length in (3,4,6):
        end=before+length
        rec={'prefill':True,'before':before,'start':0,'end':length,'prompt_end':end==13,'meta':{'length':13}}
        VLLMWorkerExtension.rq45_capture_chunk(entry,rec,q[...,before:end,:],k[...,before:end,:],8**-.5)
        assert tap.active['seen']==int(end==13)
        before=end
    assert torch.equal(tap.observed[0][0],q[...,-1:,:]) and torch.equal(tap.observed[0][1],k)
    next_q=torch.randn(1,4,1,8);next_k=torch.randn(1,2,1,8)
    VLLMWorkerExtension.rq45_capture_chunk(entry,{'prefill':False},next_q,next_k,8**-.5)
    assert tap.active['seen']==2 and torch.equal(tap.observed[1][1],torch.cat((k,next_k),dim=-2))
    VLLMWorkerExtension.rq45_capture_chunk(entry,{'prefill':False},next_q,next_k,8**-.5)
    assert len(tap.observed)==2 and 'attention_keys' not in entry and 'attention_key_chunks' not in entry
    for before,length,endflag in ((1,3,False),(0,14,True),(0,3,True)):
        e={'tap':Tap(),'attention_module':entry['attention_module']}
        rec={'prefill':True,'before':before,'start':0,'end':length,'prompt_end':endflag,'meta':{'length':13}}
        try:VLLMWorkerExtension.rq45_capture_chunk(e,rec,q,k if length==14 else k[...,:length,:],8**-.5)
        except ValueError:pass
        else:raise AssertionError('Invalid attention chunk accepted')
    return {'status':'passed','scope':'chunk contiguity, full prompt query, first decode query, exactly two samples, invalid chunks',
        'cases':7,'model_calls':0,'full_population_rerun':False}


def capture_partition_regression():
    """Affected synthetic checks only, not a repeat of population qualification."""
    import torch
    from types import SimpleNamespace
    from .exps import VLLMWorkerExtension as W
    base=chunked_capture_regression()
    torch.manual_seed(4512)
    h=torch.randn(9,8);pos=torch.arange(9);weights=torch.randn(8,8)
    def split(qkv,positions):return qkv,qkv*.3,qkv*.7,qkv*.2
    module=SimpleNamespace(qkv_proj=lambda x:(x@weights,None),_project_qkv_gate=split,
        attn=lambda q,k,v:torch.softmax(q@k.T/(8**.5),dim=-1)@v,o_proj=lambda x:(x@weights.T,None))
    q,k,v,g=split(h@weights,pos);expected=(torch.softmax(q@k.T/(8**.5),dim=-1)@v)*torch.sigmoid(g);expected=expected@weights.T
    output=torch.empty_like(expected);seen=[]
    W.rq45_attention_math(module,pos,output,h,lambda q,k,m:seen.append((q.clone(),k.clone())))
    assert torch.equal(output,expected) and len(seen)==1 and torch.equal(seen[0][0],q)
    W.rq45_attention_math(module,pos,output,h)
    assert torch.equal(output,expected)
    module._project_qkv_gate=lambda x,p:(x,x*.3,x*.7,None)
    W.rq45_attention_math(module,pos,output,h)
    assert torch.equal(output,(torch.softmax(q@k.T/(8**.5),dim=-1)@v)@weights.T)
    samples=[{'unix':i,'gpu_util_percent':v} for i,v in [(0,0),(1,40),(2,80),(3,0),(4,0)]]
    result=W.rq45_utilization_interval(samples,1.25,2.75)
    assert abs(result['time_weighted_mean_gpu_util_percent']-60)<1e-12 and result['coverage_fraction']==1
    try:W.rq45_utilization_interval(samples,7,8)
    except ValueError:pass
    else:raise AssertionError('Missing GPU measurements accepted')
    return {'status':'passed','cases':base['cases']+5,'scope':'native gated/ungated layer arithmetic, passive read, exact chunked queries, GPU interval exclusion/integration',
        'model_calls':0,'full_population_rerun':False,'GPU_compilation_and_NVML':'requires new actual smoke'}


def gpu_identity_regression():
    """Only the affected device-identity and sampling-window logic; no model."""
    from .exps import VLLMWorkerExtension as W
    value='1a2b3c4d-5678-90ab-cdef-0123456789ab';expected='GPU-'+value
    variants=[value,value.upper(),'GPU-'+value,'gpu-'+value.upper(),('GPU-'+value).encode('ascii'),' '+value+' ']
    for v in variants:assert W.rq45_canonical_gpu_uuid(v)==expected
    other='GPU-1a2b3c4d-5678-90ab-cdef-0123456789ac'
    assert W.rq45_canonical_gpu_uuid(other)!=expected
    for invalid in ['GPU-not-a-uuid','',None,'GPU-01234']:
        try:W.rq45_canonical_gpu_uuid(invalid)
        except (ValueError,UnicodeError):pass
        else:raise AssertionError('Malformed device identity accepted')
    result=W.rq45_utilization_interval([{'unix':i,'gpu_util_percent':v} for i,v in [(0,0),(1,40),(2,80),(3,0)]],1.25,2.75)
    assert result['time_weighted_mean_gpu_util_percent']==60. and result['coverage_fraction']==1.
    return {'status':'passed','cases':12,'scope':'UUID format equivalence, distinct/malformed device rejection, inference-only GPU integration',
        'model_calls':0,'full_population_rerun':False,'native_model_math_changed':False}


def graph_dispatch_boundary_regression(dispatcher_path,adapter_source=None):
    """Execute the real guard and installed native dispatch using CPU-only state.

    No torch/vLLM import, weights, GPU, or telemetry preparation is required.
    Shapes imitate a one-token prefill tail and decode mixtures; this does not
    claim to execute a CUDA graph or replace native GPU qualification.
    """
    import ast
    from pathlib import Path
    from enum import IntEnum
    from dataclasses import dataclass,replace
    from types import SimpleNamespace
    class Mode(IntEnum):
        NONE=0
        PIECEWISE=1
        FULL=2
        @classmethod
        def valid_runtime_modes(cls):return {cls.NONE,cls.PIECEWISE,cls.FULL}
        def separate_routine(self):return True
    @dataclass(frozen=True)
    class BatchDescriptor:
        num_tokens:int
        num_reqs:int=None
        uniform:bool=False
    tree=ast.parse(Path(dispatcher_path).read_text())
    native=next(n for c in tree.body if isinstance(c,ast.ClassDef)
                for n in c.body if isinstance(n,ast.FunctionDef) and n.name=='dispatch')
    native.decorator_list=[];native.returns=None
    for arg in native.args.args+native.args.kwonlyargs:arg.annotation=None
    native_env={'CUDAGraphMode':Mode,'BatchDescriptor':BatchDescriptor,'replace':replace}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[native],type_ignores=[])),str(dispatcher_path),'exec'),native_env)
    dispatcher=SimpleNamespace(keys_initialized=True,cudagraph_mode=Mode.FULL,
        compilation_config=SimpleNamespace(max_cudagraph_capture_size=8),
        cudagraph_keys={Mode.FULL:{BatchDescriptor(n,n,True) for n in range(1,9)},
                       Mode.PIECEWISE:{BatchDescriptor(n,None,False) for n in range(1,9)}},
        _create_padded_batch_descriptor=lambda n,uniform,lora,active:BatchDescriptor(n,n if uniform else None,uniform))
    text=adapter_source if adapter_source is not None else Path(__file__).with_name('exps.py').read_text()
    guard=next(n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name=='guarded_dispatch')
    def run(prefills,seen=None,valid=None,invalid=None,broken_dispatch=False):
        records=[{'key':str(i),'prefill':p,'start':i,'end':i+1} for i,p in enumerate(prefills)]
        state={'requests':{r['key']:{'tap':None if seen is None else SimpleNamespace(active={'seen':seen})} for r in records},
               'attention_eager_batches':0,'compiled_path_batches':0,'capture_compiled_batches':0,'graph_decode_batches':0}
        passed=[]
        def dispatch(*args,**kwargs):
            passed.append({k:set(v) if isinstance(v,set) else v for k,v in kwargs.items()})
            if broken_dispatch:return Mode.FULL,None
            return native_env['dispatch'](dispatcher,*args,**kwargs)
        env={'prepare_records':lambda:records,'state':state,'dispatch':dispatch,'CUDAGraphMode':Mode}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[guard],type_ignores=[])),str(Path(__file__)),'exec'),env)
        valid_original=None if valid is None else set(valid);invalid_original=None if invalid is None else set(invalid)
        result=env['guarded_dispatch'](num_tokens=max(1,len(records)),uniform_decode=True,valid_modes=valid,invalid_modes=invalid)
        assert valid==valid_original and invalid==invalid_original,'Caller mode sets mutated'
        return result[0],state,passed
    checks=[]
    def check(name,expected,*args,**kwargs):
        mode,state,passed=run(*args,**kwargs);assert mode==expected,(name,mode,expected)
        checks.append(name)
    check('one-token prefill tail without attention',Mode.PIECEWISE,[True])
    check('one-token prefill tail mixed with seven decodes',Mode.PIECEWISE,[False]*7+[True])
    check('ordinary decode keeps FULL acceleration',Mode.FULL,[False]*8)
    check('capture pending in prefill',Mode.PIECEWISE,[True],seen=0)
    check('first decode capture pending',Mode.PIECEWISE,[False],seen=1)
    check('finished two-query capture keeps FULL',Mode.FULL,[False],seen=2)
    check('caller force-eager restriction remains',Mode.NONE,[False],seen=1,valid={Mode.NONE})
    check('caller disables PIECEWISE',Mode.NONE,[True],invalid={Mode.PIECEWISE})
    check('caller disallows NONE but allows PIECEWISE',Mode.PIECEWISE,[True],valid={Mode.PIECEWISE,Mode.FULL},invalid={Mode.NONE})
    check('no live records preserves native path',Mode.FULL,[])
    try:run([True],valid={Mode.FULL})
    except RuntimeError as exc:assert 'No safe graph mode' in str(exc)
    else:raise AssertionError('Conflicting native restrictions silently widened')
    checks.append('incompatible caller restrictions fail closed')
    try:run([True],broken_dispatch=True)
    except RuntimeError as exc:assert 'Unsafe graph replay' in str(exc)
    else:raise AssertionError('Unsafe FULL result was accepted')
    checks.append('post-dispatch safety assertion retained')
    return {'status':'passed','cases':len(checks),'checks':checks,'model_calls':0,
            'native_dispatch_source':str(dispatcher_path),'scope':'real guard plus installed native dispatcher, synthetic CPU batch state',
            'full_population_rerun':False,'GPU_graph_execution':'not run'}


def recovery_identity_regression():
    """Reviewed source transition appends attempts; prior failure never mutates."""
    from pathlib import Path
    import tempfile,copy
    from .utils import serialized_call_register,reviewed_retry_matches
    with tempfile.TemporaryDirectory(prefix='rq45-retry-') as tmp:
        ledger=serialized_call_register(Path(tmp)/'calls.sqlite',10,'rq45_formal',10)
        try:
            first,_=ledger.begin('case','old','RCA');ledger.finish(first,{'error':'original fatal graph guard'},'infrastructure_failure')
            with ledger.connect() as db:
                original=db.execute('SELECT * FROM calls ORDER BY id').fetchall()
                row=db.execute('SELECT id,request_hash,state,result,role FROM calls ORDER BY id DESC LIMIT 1').fetchone()
            receipt={'authorized':True,'requests':{'rq45_formal/case':{'failed_attempt_id':first,'old_request_hash':'old','new_request_hash':'new','role':'RCA'}}}
            assert reviewed_retry_matches('rq45_formal/case','new','RCA',row,receipt)
            assert not reviewed_retry_matches('rq45_formal/case','wrong','RCA',row,receipt)
            assert not reviewed_retry_matches('rq45_formal/case','new','QA',row,receipt)
            assert not reviewed_retry_matches('rq45_formal/other','new','RCA',row,receipt)
            assert not reviewed_retry_matches('rq45_formal/case','new','RCA',row,dict(receipt,authorized=False))
            for field,value in [(0,first+1),(1,'wrong'),(2,'complete')]:
                altered=list(row);altered[field]=value
                assert not reviewed_retry_matches('rq45_formal/case','new','RCA',altered,receipt)
            try:ledger.cached('case','new','RCA',retry=True)
            except ValueError:pass
            else:raise AssertionError('Unapproved generation identity transition accepted')
            ledger.retry_receipt=receipt
            assert ledger.cached('case','new','RCA',retry=True) is None
            second,cached=ledger.begin('case','new','RCA',retry=True)
            assert second==first+1 and cached is None
            with ledger.connect() as db:assert db.execute('SELECT * FROM calls ORDER BY id').fetchall()[:1]==original
            try:ledger.begin('case','new','RCA',retry=True)
            except RuntimeError:pass
            else:raise AssertionError('Concurrent duplicate attempt accepted')
            ledger.finish(second,{'response':'preserved new completion'})
            assert ledger.cached('case','new','RCA',retry=True)=={'response':'preserved new completion'}
            assert not ledger.reviewed_retry_eligible('case','new','RCA')
            assert ledger.begin('case','new','RCA',retry=True)==(None,{'response':'preserved new completion'})
            assert ledger.summary()=={'complete':1,'infrastructure_failure':1}
        finally:ledger.close()
    return {'status':'passed','checks':14,'scope':'attempt/hash/role-bound permission, append-only retry, completed reuse, duplicate exclusion and preserved original failures','model_calls':0}
